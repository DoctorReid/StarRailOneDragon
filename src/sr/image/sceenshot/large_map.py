import os
from typing import List

import cv2
import numpy as np
from cv2.typing import MatLike

from basic import os_utils, str_utils, Point, Rect
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr import const
from sr.config import game_config
from sr.const import game_config_const
from sr.const.map_const import Planet, Region, PLANET_LIST
from sr.image import TemplateImage, ImageMatcher, get_large_map_dir_path
from sr.image.ocr_matcher import OcrMatcher
from sr.image.image_holder import ImageHolder
from sr.image.sceenshot import LargeMapInfo

PLANET_NAME_RECT = Rect(100, 60, 350, 100)
CUT_MAP_RECT = Rect(200, 190, 1300, 900)  # 截取大地图的区域
EMPTY_MAP_POS = Point(1350, 800)  # 地图空白区域 用于取消选择传送点 和 拖动地图
TP_BTN_RECT = Rect(1500, 950, 1800, 1000)  # 右侧显示传送按钮的区域
REGION_LIST_RECT = Rect(1480, 200, 1820, 1000)
FLOOR_LIST_PART = Rect(30, 730, 100, 1000)

LARGE_MAP_POWER_RECT = Rect(1650, 54, 1690, 75)  # 大地图上显示体力的位置


def get_planet(screen: MatLike, ocr: OcrMatcher) -> Planet:
    """
    从屏幕左上方 获取当前星球的名字
    :param screen: 屏幕截图
    :param ocr: ocr
    :return: 星球名称
    """
    planet_name_part, _ = cv2_utils.crop_image(screen, PLANET_NAME_RECT)
    planet_name_str: str = ocr.ocr_for_single_line(planet_name_part)

    log.debug('屏幕左上方获取星球结果 %s', planet_name_str)
    if planet_name_str is not None:
        for p in PLANET_LIST:
            if str_utils.find_by_lcs(gt(p.cn, 'ocr'), planet_name_str, percent=game_config.get().planet_lcs_percent):
                return p

    return None


def cut_minus_or_plus(screen: MatLike, minus: bool = True) -> MatLike:
    """
    从大地图下方把减号/加号裁剪出来
    :param screen: 大地图截图
    :param minus: 是否要减号
    :return: 减号/加号图片 掩码图
    """
    op_part = screen[960: 1010, 600: 650] if minus else screen[960: 1010, 970: 1020]
    gray = cv2.cvtColor(op_part, cv2.COLOR_BGR2GRAY)
    _, bw = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    # 做一个连通性检测 将黑色噪点消除
    bw = cv2_utils.connection_erase(bw, erase_white=False)
    cv2_utils.show_image(bw, win_name='bw')
    circles = cv2.HoughCircles(bw, cv2.HOUGH_GRADIENT, 1, 20, param1=0.7, param2=0.7, maxRadius=15)
    # 如果找到了圆
    tx, ty, tr = 0, 0, 0
    if circles is not None:
        circles = np.uint8(np.around(circles))

        # 保留半径最大的圆
        for circle in circles[0, :]:
            if circle[2] > tr:
                tx, ty, tr = circle[0], circle[1], circle[2]

    show_circle = op_part.copy()
    cv2.circle(show_circle, (tx, ty), tr, (255, 0, 0), 2)

    ml = (tr + 5) * 2
    mask = np.zeros((ml, ml), dtype=np.uint8)
    cv2.circle(mask, (ml // 2, ml // 2), tr + 1, 255, -1)

    cv2_utils.show_image(show_circle, win_name='op_part')
    cv2_utils.show_image(mask, win_name='mask')
    cut = op_part[ty-tr-5:ty+tr+5, tx-tr-5:tx+tr+5]
    cut = cv2.bitwise_and(cut, cut, mask=mask)
    cv2_utils.show_image(cut, win_name='cut')
    return cut, mask


def get_sp_mask_by_template_match(lm_info: LargeMapInfo, im: ImageMatcher,
                                  template_type: str = 'origin',
                                  template_list: List = None,
                                  show: bool = False):
    """
    在地图中 圈出传送点、商铺点等可点击交互的的特殊点
    使用模板匹配
    :param lm_info: 大地图
    :param im: 图片匹配器
    :param template_type: 模板类型
    :param template_list: 限定种类的特殊点
    :param show: 是否展示结果
    :return: 特殊点组成的掩码图 特殊点是白色255、特殊点的匹配结果
    """
    sp_match_result = {}
    source = lm_info.origin if template_type == 'origin' else lm_info.gray
    sp_mask = np.zeros(source.shape[:2], dtype=np.uint8)
    # 找出特殊点位置
    for prefix in ['mm_tp', 'mm_sp', 'mm_boss']:
        for i in range(100):
            if i == 0:
                continue
            template_id = '%s_%02d' % (prefix, i)
            if template_list is not None and template_id not in template_list:
                continue
            ti: TemplateImage = im.get_template(template_id)
            if ti is None:
                break
            template = ti.get(template_type)
            template_mask = ti.mask

            match_result = im.match_image(
                source, template, mask=template_mask,
                threshold=const.THRESHOLD_SP_TEMPLATE_IN_LARGE_MAP,
                only_best=False,
                ignore_inf=True)

            if len(match_result) > 0:
                sp_match_result[template_id] = match_result
            for r in match_result:
                sp_mask[r.y:r.y+r.h, r.x:r.x+r.w] = cv2.bitwise_or(sp_mask[r.y:r.y+r.h, r.x:r.x+r.w], template_mask)

            if show:
                cv2_utils.show_image(source, win_name='source_%s' % template_id)
                cv2_utils.show_image(template, win_name='template_%s' % template)
                cv2_utils.show_image(source, match_result, win_name='all_match_%s' % template_id)
                cv2.waitKey(0)
                cv2.destroyAllWindows()

    return sp_mask, sp_match_result


def get_map_path(region: Region, mt: str = 'origin') -> str:
    """
    获取某张地图路径
    :param region: 对应区域
    :param mt: 地图类型
    :return: 图片路径
    """
    return os.path.join(os_utils.get_path_under_work_dir('images', 'map', region.planet.np_id, region.rl_id), '%s.png' % mt)


def save_large_map_image(image: MatLike, region: Region, mt: str = 'origin'):
    """
    保存某张地图
    :param image: 图片
    :param region: 区域
    :param mt: 地图类型
    :return:
    """
    path = get_map_path(region, mt)
    cv2.imwrite(path, image)


def get_active_region_name(screen: MatLike, ocr: OcrMatcher) -> str:
    """
    在大地图界面 获取右边列表当前选择的区域 白色字体
    :param screen: 大地图界面截图
    :param ocr: ocr
    :return: 当前选择区域
    """
    lower = 240
    upper = 255
    part, _ = cv2_utils.crop_image(screen, REGION_LIST_RECT)
    bw = cv2.inRange(part, (lower, lower, lower), (upper, upper, upper))
    left, right, top, bottom = cv2_utils.get_four_corner(bw)
    if left is None:
        return None
    rect = Rect(left[0] - 10, top[1] - 10, right[0] + 10, bottom[1] + 10)
    to_ocr: MatLike = cv2_utils.crop_image(bw, rect)[0]
    # cv2_utils.show_image(to_ocr, win_name='get_active_region_name')
    return ocr.ocr_for_single_line(to_ocr, strict_one_line=False)


def get_active_floor(screen: MatLike, ocr: OcrMatcher) -> str:
    """
    在大地图界面 获取左下方当前选择的层数 黑色字体
    :param screen: 大地图界面截图
    :param ocr: ocr
    :return: 当前选择区域
    """
    lower = 40
    upper = 80
    part, _ = cv2_utils.crop_image(screen, FLOOR_LIST_PART)
    bw = cv2.inRange(part, (lower, lower, lower), (upper, upper, upper))
    km = ocr.run_ocr(bw)
    if len(km) > 0:
        return km.popitem()[0]
    else:
        return None


def init_large_map(region: Region, raw: MatLike, im: ImageMatcher,
                   expand_arr: List = None,
                   save: bool = False) -> LargeMapInfo:
    """
    初始化大地图需要用的数据
    :param region: 区域
    :param raw: 大地图原始图片
    :param im: 图片处理器
    :param expand_arr: 需要拓展的大小
    :param save: 是否保存
    :return:
    """
    info = LargeMapInfo()
    info.region = region
    info.raw = raw
    if expand_arr is None:
        expand_arr = get_expand_arr(raw)
    info.origin = expand_raw(raw, expand_arr)
    gray = cv2.cvtColor(info.origin, cv2.COLOR_BGRA2GRAY)
    sp_mask, info.sp_result = get_sp_mask_by_template_match(info, im)
    road_mask = get_large_map_road_mask(info.origin, sp_mask)
    info.gray, info.mask = merge_all_map_mask(gray, road_mask, sp_mask)
    info.kps, info.desc = cv2_utils.feature_detect_and_compute(info.gray, mask=info.mask)

    if save:
        cv2_utils.show_image(info.origin, win_name='origin')
        cv2_utils.show_image(info.gray, win_name='gray')
        cv2_utils.show_image(info.mask, win_name='mask')
        log.info('地图特殊点坐标')
        i: int = 0
        for k, v in info.sp_result.items():
            for vs in v:
                log.info("SP%02d = TransportPoint('', '', , '%s', %s)", i+1, k, vs.center)
                i += 1

        cv2.waitKey(0)

        save_large_map_image(info.origin, region, 'origin')
        save_large_map_image(info.gray, region, 'gray')
        save_large_map_image(info.mask, region, 'mask')

        dir_path = get_large_map_dir_path(region)
        file_storage = cv2.FileStorage(os.path.join(dir_path, 'features.xml'), cv2.FILE_STORAGE_WRITE)
        # 保存特征点和描述符
        file_storage.write("keypoints", cv2_utils.feature_keypoints_to_np(info.kps))
        file_storage.write("descriptors", info.desc)
        file_storage.release()

    return info


def get_expand_arr(raw: MatLike):
    """
    如果道路太贴近大地图边缘 使用小地图模板匹配的时候会匹配失败
    如果最后截图高度或宽度跟大地图圈定范围CUT_MAP_RECT一致 则choose_transport_point中两个大地图做模板匹配可能会报错
    这些情况需要拓展一下大地图
    :param raw: 大地图原图
    :return: 各个方向需要扩展的大小
    """
    # 道路掩码图
    mask: MatLike = get_large_map_road_mask(raw)

    mm_pos = game_config.get().mini_map_pos
    padding = mm_pos.r + 10  # 边缘至少留一个小地图半径的空白

    # 四个方向需要拓展多少像素
    left, right, top, bottom = cv2_utils.get_four_corner(mask)
    lp = 0 if left[0] >= padding else padding - left[0]
    rp = 0 if right[0] + padding < raw.shape[1] else right[0] + padding + 1 - raw.shape[1]
    tp = 0 if top[1] >= padding else padding - top[1]
    bp = 0 if bottom[1] + padding < raw.shape[0] else bottom[1] + padding + 1 - raw.shape[0]

    # raw 尺寸至少跟CUT_MAP_RECT一致 所以只有上面没有拓展的情况要
    if tp == 0 and bp == 0 and raw.shape[0] == CUT_MAP_RECT.y2 - CUT_MAP_RECT.y1:
        tp = 5
        bp = 5
    if lp == 0 and rp == 0 and raw.shape[1] == CUT_MAP_RECT.x2 - CUT_MAP_RECT.x1:
        lp = 5
        rp = 5

    return lp, rp, tp, bp


def expand_raw(raw: MatLike, expand_arr: List = None):
    """
    如果道路太贴近大地图边缘 使用小地图模板匹配的时候会匹配失败
    这时候需要拓展一下大地图
    :param raw: 大地图原图
    :param expand_arr: 需要拓展的大小
    :return:
    """
    lp = expand_arr[0]
    rp = expand_arr[1]
    tp = expand_arr[2]
    bp = expand_arr[3]
    if lp == 0 and rp == 0 and tp == 0 and bp == 0:
        return raw.copy()

    origin = np.full((raw.shape[0] + tp + bp, raw.shape[1] + lp + rp, raw.shape[2]),
                     fill_value=210, dtype=np.uint8)
    origin[tp:tp+raw.shape[0], lp:lp+raw.shape[1]] = raw

    return origin


def get_large_map_road_mask(map_image: MatLike,
                            sp_mask: MatLike = None) -> MatLike:
    """
    在地图中 按接近道路的颜色圈出地图的主体部分 过滤掉无关紧要的背景
    :param map_image: 地图图片
    :param sp_mask: 特殊点的掩码 道路掩码应该排除这部分
    :return: 道路掩码图 能走的部分是白色255
    """
    # 按道路颜色圈出 当前层的颜色
    l1 = 45
    u1 = 100
    lower_color = np.array([l1, l1, l1], dtype=np.uint8)
    upper_color = np.array([u1, u1, u1], dtype=np.uint8)
    road_mask_1 = cv2.inRange(map_image, lower_color, upper_color)
    # 按道路颜色圈出 其他层的颜色
    l2 = 120
    u2 = 150
    lower_color = np.array([l2, l2, l2], dtype=np.uint8)
    upper_color = np.array([u2, u2, u2], dtype=np.uint8)
    road_mask_2 = cv2.inRange(map_image, lower_color, upper_color)

    road_mask = cv2.bitwise_or(road_mask_1, road_mask_2)

    # 合并特殊点进行连通性检测
    to_check_connection = cv2.bitwise_or(road_mask, sp_mask) if sp_mask is not None else road_mask

    # 非道路连通块 < 50的(小的黑色块) 认为是噪点 加入道路
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(cv2.bitwise_not(to_check_connection), connectivity=4)
    large_components = []
    for label in range(1, num_labels):
        if stats[label, cv2.CC_STAT_AREA] < 50:
            large_components.append(label)
    for label in large_components:
        to_check_connection[labels == label] = 255

    # 找到多于500个像素点的连通道路(大的白色块) 这些才是真的路
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(to_check_connection, connectivity=4)
    large_components = []
    for label in range(1, num_labels):
        if stats[label, cv2.CC_STAT_AREA] > 500:
            large_components.append(label)
    real_road_mask = np.zeros(map_image.shape[:2], dtype=np.uint8)
    for label in large_components:
        real_road_mask[labels == label] = 255

    # 排除掉特殊点
    if sp_mask is not None:
        real_road_mask = cv2.bitwise_and(real_road_mask, cv2.bitwise_not(sp_mask))

    return real_road_mask


def merge_all_map_mask(gray_image: MatLike, road_mask, sp_mask):
    """
    :param gray_image:
    :param road_mask:
    :param sp_mask:
    :return:
    """
    usage = gray_image.copy()

    # 稍微膨胀一下
    kernel = np.ones((5, 5), np.uint8)
    expand_sp_mask = cv2.dilate(sp_mask, kernel, iterations=1)

    all_mask = cv2.bitwise_or(road_mask, expand_sp_mask)
    usage[np.where(all_mask == 0)] = const.COLOR_WHITE_GRAY
    usage[np.where(road_mask == 255)] = const.COLOR_MAP_ROAD_GRAY
    return usage, all_mask


def get_edge_mask(road_mask: MatLike):
    """
    大地图道路边缘掩码 暂时不需要
    :param road_mask:
    :return:
    """
    # return cv2.Canny(road_mask, threshold1=200, threshold2=230)

    # 查找轮廓
    contours, hierarchy = cv2.findContours(road_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # 创建空白图像作为绘制轮廓的画布
    edge_mask = np.zeros_like(road_mask)
    # 绘制轮廓
    cv2.drawContours(edge_mask, contours, -1, 255, 2)
    return edge_mask


def get_large_map_rect_by_pos(lm_shape, mm_shape, possible_pos: tuple = None) -> Rect:
    """
    :param lm_shape: 大地图尺寸
    :param mm_shape: 小地图尺寸
    :param possible_pos: 可能在大地图的位置 (x,y,d)。 (x,y) 是上次在的位置 d是移动的距离
    :return:
    """
    if possible_pos is not None:  # 传入了潜在位置 那就截取部分大地图再进行匹配
        mr = mm_shape[0] // 2  # 小地图半径
        x, y = int(possible_pos[0]), int(possible_pos[1])
        # 还没有移动的话 通常是第一个点 这时候先默认移动1秒距离判断
        r = 20 if len(possible_pos) < 3 or possible_pos[2] == 0 else int(possible_pos[2])
        ur = r + 20 + mr + 5  # 潜在位置半径 = 移动距离 + 20(1秒移动距离) + 小地图半径 + 5(多留一些边缘匹配)
        lm_offset_x = x - ur
        lm_offset_y = y - ur
        lm_offset_x2 = x + ur
        lm_offset_y2 = y + ur
        if lm_offset_x < 0:  # 防止越界
            lm_offset_x = 0
        if lm_offset_y < 0:
            lm_offset_y = 0
        if lm_offset_x2 > lm_shape[1]:
            lm_offset_x2 = lm_shape[1]
        if lm_offset_y2 > lm_shape[0]:
            lm_offset_y2 = lm_shape[0]
        return Rect(lm_offset_x, lm_offset_y, lm_offset_x2, lm_offset_y2)
    else:
        return None


def analyse_large_map(region: Region, ih: ImageHolder):
    """
    预处理 从大地图中提取出所有需要的信息
    :param region: 区域
    :param ih: 图片加载器
    :return:
    """
    info = ih.get_large_map(region)
    return info


def get_road_edge_mask(road_mask: MatLike):
    """
    大地图道路边缘掩码 暂时不需要
    :param road_mask:
    :return:
    """
    # 查找轮廓
    contours, hierarchy = cv2.findContours(road_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # 创建空白图像作为绘制轮廓的画布
    edge_mask = np.zeros_like(road_mask)
    # 绘制轮廓
    cv2.drawContours(edge_mask, contours, -1, 255, 1)

    return edge_mask
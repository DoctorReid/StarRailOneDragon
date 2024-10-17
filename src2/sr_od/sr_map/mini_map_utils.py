import math
import os
import time
from functools import lru_cache
from typing import Set, Optional, List, Tuple

import cv2
import numpy as np
from cv2.typing import MatLike

from one_dragon.base.geometry.point import Point
from one_dragon.base.matcher.match_result import MatchResultList, MatchResult
from one_dragon.base.screen.template_info import TemplateInfo
from one_dragon.utils import cv2_utils, os_utils, cal_utils
from one_dragon.utils.log_utils import log
from sr_od.config import game_const
from sr_od.config.game_config import MiniMapPos
from sr_od.context.sr_context import SrContext
from sr_od.sr_map import mini_map_angle_alas
from sr_od.sr_map.mini_map_info import MiniMapInfo
from src.sr.image import TemplateImage


def cal_little_map_pos(screen: MatLike) -> MiniMapPos:
    """
    计算小地图的坐标
    通过截取屏幕左上方部分 找出最大的圆圈 就是小地图。
    部分场景无法准确识别 所以使用一次校准后续读取配置使用。
    最容易匹配地点在【空间站黑塔】【基座舱段】【接待中心】传送点
    :param screen: 屏幕截图
    """
    # 左上角部分
    x, y = 0, 0
    x2, y2 = 340, 380
    image = screen[y:y2, x:x2]

    # 对图像进行预处理
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1.2, 100, minRadius=80, maxRadius=100)  # 小地图大概的圆半径

    # 如果找到了圆
    if circles is not None:
        circles = np.uint16(np.around(circles))
        tx, ty, tr = 0, 0, 0

        # 保留半径最大的圆
        for circle in circles[0, :]:
            if circle[2] > tr:
                tx, ty, tr = circle[0], circle[1], circle[2]

        mm_pos = MiniMapPos(tx, ty, tr)
        log.debug('计算小地图所在坐标为 %s', mm_pos)
        return mm_pos
    else:
        log.error('无法找到小地图的圆')


def cut_mini_map(screen: MatLike, mm_pos: MiniMapPos) -> MatLike:
    """
    从整个游戏窗口截图中 裁剪出小地图部分
    :param screen: 屏幕截图
    :param mm_pos: 小地图位置的配置
    :return:
    """
    return screen[mm_pos.ly:mm_pos.ry, mm_pos.lx:mm_pos.rx]


def preheat():
    """
    预热缓存
    :return:
    """
    for i in range(93, 100):  # 不同时期截图大小可能不一致
        mini_map_angle_alas.RotationRemapData(i * 2)

    for i in range(int(360 // 1.875)):
        get_radio_to_del(i * 1.875)


def extract_arrow(mini_map: MatLike):
    """
    提取小箭头部分 范围越小越精准
    :param mini_map: 小地图
    :return: 小箭头
    """
    return cv2_utils.color_similarity_2d(mini_map, game_const.COLOR_ARROW_BGR)


def get_arrow_mask(mm: MatLike):
    """
    获取小地图的小箭头掩码
    :param mm: 小地图
    :return: 中心区域的掩码 和 整张图的掩码
    """
    w, h = mm.shape[1], mm.shape[0]
    cx, cy = w // 2, h // 2
    d = game_const.TEMPLATE_ARROW_LEN
    r = game_const.TEMPLATE_ARROW_R
    center = mm[cy - r:cy + r, cx - r:cx + r]
    arrow = extract_arrow(center)
    _, mask = cv2.threshold(arrow, 180, 255, cv2.THRESH_BINARY)
    # 做一个连通性检测 小于50个连通的认为是噪点
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    large_components = []
    for label in range(1, num_labels):
        if stats[label, cv2.CC_STAT_AREA] < 50:
            large_components.append(label)
    for label in large_components:
        mask[labels == label] = 0

    whole_mask = np.zeros((h,w), dtype=np.uint8)
    whole_mask[cy-r:cy+r, cx-r:cx+r] = mask
    # 黑色边缘线条采集不到 稍微膨胀一下
    kernel = np.ones((5, 5), np.uint8)
    cv2.dilate(src=whole_mask, dst=whole_mask, kernel=kernel, iterations=1)
    arrow_mask, _ = cv2_utils.convert_to_standard(mask, mask, width=d, height=d)
    return arrow_mask, whole_mask


def analyse_arrow_and_angle(mini_map: MatLike):
    """
    在小地图上获取小箭头掩码和角度
    没有性能问题
    :param mini_map: 小地图图片
    :return:
    """
    center_arrow_mask, arrow_mask = get_arrow_mask(mini_map)
    angle = mini_map_angle_alas.calculate(mini_map)
    return center_arrow_mask, arrow_mask, angle


def analyse_angle(mini_map: MatLike) -> float:
    return mini_map_angle_alas.calculate(mini_map)


def init_sp_mask_by_feature_match(ctx: SrContext, mm_info: MiniMapInfo,
                                  sp_types: Set = None,
                                  show: bool = False):
    """
    在小地图上找到特殊点 使用特征匹配 每个模板最多只能找到一个
    特征点提取匹配、画掩码耗时都很少 主要花费在读模板 真实运行有缓存就没问题
    :param ctx: 上下文
    :param mm_info: 小地图信息
    :param sp_types: 限定种类的特殊点
    :param show: 是否展示结果
    :return:
    """
    if mm_info.sp_mask is not None:
        return

    sp_mask = np.zeros_like(mm_info.circle_mask)
    sp_match_result = {}

    if sp_types is None or len(sp_types) == 0:  # 没有特殊点
        mm_info.sp_mask = sp_mask
        mm_info.sp_result = sp_match_result
        return

    source = mm_info.origin_del_radio
    source_mask = mm_info.circle_mask
    source_kps, source_desc = cv2_utils.feature_detect_and_compute(source, mask=source_mask)
    for prefix in ['mm_tp', 'mm_sp', 'mm_boss', 'mm_sub']:
        for i in range(100):
            if i == 0:
                continue

            template_id = '%s_%02d' % (prefix, i)
            t: TemplateInfo = ctx.template_loader.get_template(template_id)
            if t is None:
                break
            if sp_types is not None and template_id not in sp_types:
                continue

            match_result_list = MatchResultList()
            template = t.raw
            template_mask = t.mask

            template_kps, template_desc = t.features

            good_matches, offset_x, offset_y, scale = cv2_utils.feature_match(
                source_kps, source_desc,
                template_kps, template_desc,
                source_mask=source_mask)

            if offset_x is not None:
                mr = MatchResult(1, offset_x, offset_y, template.shape[1], template.shape[0], template_scale=scale)  #
                match_result_list.append(mr, auto_merge=False)
                sp_match_result[template_id] = match_result_list

                # 缩放后的宽度和高度
                sw = int(template.shape[1] * scale)
                sh = int(template.shape[0] * scale)
                # one_sp_mask = cv2.resize(template_mask, (sh, sw))
                one_sp_mask = np.zeros((sh, sw))

                rect1, rect2 = cv2_utils.get_overlap_rect(sp_mask, one_sp_mask, mr.x, mr.y)
                sx_start, sy_start, sx_end, sy_end = rect1
                tx_start, ty_start, tx_end, ty_end = rect2
                # sp_mask[sy_start:sy_end, sx_start:sx_end] = cv2.bitwise_or(
                #     sp_mask[sy_start:sy_end, sx_start:sx_end],
                #     one_sp_mask[ty_start:ty_end, tx_start:tx_end]
                # )
                sp_mask[sy_start:sy_end, sx_start:sx_end] = 255

            if show:
                cv2_utils.show_image(source, win_name='source')
                cv2_utils.show_image(source_mask, win_name='source_mask')
                source_with_keypoints = cv2.drawKeypoints(source, source_kps, None)
                cv2_utils.show_image(source_with_keypoints, win_name='source_with_keypoints_%s' % template_id)
                template_with_keypoints = cv2.drawKeypoints(template, template_kps, None)
                cv2_utils.show_image(
                    cv2.bitwise_and(template_with_keypoints, template_with_keypoints, mask=template_mask),
                    win_name='template_with_keypoints_%s' % template_id)
                all_result = cv2.drawMatches(template, template_kps, source, source_kps, good_matches, None, flags=2)
                cv2_utils.show_image(all_result, win_name='all_match_%s' % template_id)

                if offset_x is not None:
                    cv2_utils.show_overlap(source, template, offset_x, offset_y, template_scale=scale, win_name='overlap_%s' % template_id)
                cv2.waitKey(0)
                cv2.destroyAllWindows()

    mm_info.sp_mask = sp_mask
    mm_info.sp_result = sp_match_result


def is_under_attack(mm: MatLike,
                    strict: bool = False,
                    show: bool = False) -> bool:
    """
    根据小地图边缘 判断是否被锁定
    红色色道应该有一个圆
    约1ms
    :param mm: 小地图截图
    :param strict: 是否严格判断 只有红色的框认为是被锁定
    :param show: debug用 显示中间结果图片
    :return: 是否被锁定
    """
    w, h = mm.shape[1], mm.shape[0]
    cx, cy = w // 2, h // 2
    r = (cx + cy) // 2

    circle_mask = np.zeros(mm.shape[:2], dtype=np.uint8)
    cv2.circle(circle_mask, (cx, cy), r, 255, 3)

    circle_part = cv2.bitwise_and(mm, mm, mask=circle_mask)

    # 提取红色部分
    lower_color = np.array([0, 0, 200], dtype=np.uint8)
    upper_color = np.array([100, 100, 255], dtype=np.uint8)
    red = cv2.inRange(circle_part, lower_color, upper_color)

    if strict:
        mask = red
    else:
        # 提取橙色部分
        lower_color = np.array([0, 150, 200], dtype=np.uint8)
        upper_color = np.array([100, 180, 255], dtype=np.uint8)
        orange = cv2.inRange(circle_part, lower_color, upper_color)

        mask = cv2.bitwise_or(red, orange)

    circles = cv2.HoughCircles(mask, cv2.HOUGH_GRADIENT, 0.3, 100, param1=10, param2=10,
                               minRadius=r - 10, maxRadius=r + 10)
    find: bool = circles is not None

    if show:
        cv2_utils.show_image(circle_part, win_name='circle_part')
        cv2_utils.show_image(red, win_name='red')
        if not strict:
            cv2_utils.show_image(orange, win_name='orange')
        cv2_utils.show_image(mask, win_name='mask')
        find_circle = np.zeros(mm.shape[:2], dtype=np.uint8)
        if circles is not None:
            # 将检测到的圆形绘制在原始图像上
            circles = np.round(circles[0, :]).astype("int")
            for (x, y, r) in circles:
                cv2.circle(find_circle, (x, y), r, 255, 1)
        cv2_utils.show_image(find_circle, win_name='find_circle')
        cv2.waitKey(0)

    return find


mini_map_radio_to_del: Optional[MatLike] = None


@lru_cache
def get_radio_to_del(angle: Optional[float] = None):
    """
    根据人物朝向 获取对应的雷达区域颜色
    :param angle: 人物朝向
    :return:
    """
    global mini_map_radio_to_del
    if mini_map_radio_to_del is None:
        path = os.path.join(os_utils.get_path_under_work_dir('images', 'template', 'mini_map', 'mini_map_radio'), 'raw.png')
        mini_map_radio_to_del = cv2_utils.read_image(path)
    if angle is not None:
        return cv2_utils.image_rotate(mini_map_radio_to_del, 360 - angle)
    else:
        return mini_map_radio_to_del


def analyse_mini_map(origin: MatLike) -> MiniMapInfo:
    """
    预处理 从小地图中提取出所有需要的信息
    :param origin: 小地图 左上角的一个正方形区域
    :return:
    """
    info = MiniMapInfo()
    info.origin = origin
    info.center_arrow_mask, info.arrow_mask, info.angle = analyse_arrow_and_angle(origin)
    info.origin_del_radio = remove_radio(info.origin, get_radio_to_del(info.angle))
    init_circle_mask(info)

    return info


def init_circle_mask(mm_info: MiniMapInfo):
    h, w = mm_info.arrow_mask.shape[1], mm_info.arrow_mask.shape[0]
    cx, cy = w // 2, h // 2

    mm_info.circle_mask = np.zeros_like(mm_info.arrow_mask)
    cv2.circle(mm_info.circle_mask, (cx, cy), h // 2 - 5, 255, -1)  # 忽略一点圆的边缘


def remove_radio(mm: MatLike, radio_to_del: MatLike) -> MatLike:
    origin = mm.copy()
    if radio_to_del is not None:
        radius = radio_to_del.shape[0] // 2
        d = radio_to_del.shape[0]

        x1 = origin.shape[1] // 2 - radius
        x2 = x1 + d
        y1 = origin.shape[1] // 2 - radius
        y2 = y1 + d

        overlap = np.zeros_like(radio_to_del, dtype=np.uint16)
        overlap[:, :] = origin[y1:y2, x1:x2]
        overlap[:, :] -= radio_to_del
        overlap[np.where(origin[y1:y2, x1:x2] < radio_to_del)] = 0
        origin[y1:y2, x1:x2] = overlap.astype(dtype=np.uint8)

    # cv2_utils.show_image(origin, win_name='origin')
    return origin


def init_road_mask_for_world_patrol(mm_info: MiniMapInfo, another_floor: bool = False):
    """
    获取道路掩码 用于原图的模板匹配
    不考虑特殊点
    :param mm_info: 小地图信息
    :param another_floor: 可能有另一层的地图
    :return:
    """
    if mm_info.road_mask is not None:
        return

    mm_del_radio = mm_info.origin_del_radio
    b, g, r = cv2.split(mm_del_radio)

    l = 45
    u = 70  # 背景色 正常是55~60附近 太亮的时候会到达这个值 或者其它楼层也会达到这个值
    lower_color = np.array([l, l, l], dtype=np.uint8)
    upper_color = np.array([u, u, u], dtype=np.uint8)
    road_mask_1 = cv2.inRange(mm_del_radio, lower_color, upper_color)  # 这是粗略的道路掩码
    # cv2_utils.show_image(road_mask_1, win_name='road_mask_1')

    max_rgb = np.max(mm_del_radio, axis=2)
    min_rgb = np.min(mm_del_radio, axis=2)
    road_mask_cf = np.zeros(road_mask_1.shape, dtype=np.uint8)
    road_mask_cf[(max_rgb - min_rgb) <= 1] = 255  # rgb颜色差不超过1 当前层的道路就是这个颜色
    # cv2_utils.show_image(road_mask_cf, win_name='road_mask_cf')
    b_g = None
    if another_floor:  # 多层地图时 另一层的颜色是递进的 R<=G<=B 且差值在2以内
        b_g = b - g
        g_r = g - r
        road_mask_af = np.zeros(road_mask_1.shape, dtype=np.uint8)
        road_mask_af[(b_g >= 0) & (b_g <= 2) & (g_r >= 0) & (g_r <= 2)] = 255
        # cv2_utils.show_image(road_mask_af, win_name='road_mask_af')

        road_mask_floor = cv2.bitwise_or(road_mask_cf, road_mask_af)
    else:
        road_mask_floor = road_mask_cf

    road_mask_2 = cv2.bitwise_and(road_mask_1, road_mask_floor)  # 不同楼层的地图
    # cv2_utils.show_image(road_mask_2, win_name='road_mask_2')

    if b_g is None:
        b_g = b - g
    # 算敌人的掩码图
    lower_color = np.array([45, 45, 80], dtype=np.uint8)
    upper_color = np.array([70, 70, 255], dtype=np.uint8)
    enemy_mask_1 = cv2.inRange(mm_del_radio, lower_color, upper_color)  # 这是粗略的敌人图
    enemy_mask_2 = np.zeros(road_mask_1.shape, dtype=np.uint8)
    enemy_mask_2[(b_g <= 2) | (b_g >= -2)] = 255  # 敌人的雷达图 g 约等于 b
    enemy_mask = cv2.bitwise_and(enemy_mask_1, enemy_mask_2)
    # cv2_utils.show_image(enemy_mask, win_name='enemy_mask')

    mm_info.road_mask = cv2.bitwise_or(road_mask_2, enemy_mask)
    mm_info.road_mask = cv2.bitwise_and(mm_info.road_mask, mm_info.circle_mask)  # 只考虑圆形内部分

    lower_color = np.array([160, 160, 160], dtype=np.uint8)
    upper_color = np.array([210, 210, 210], dtype=np.uint8)
    edge_mask_rough = cv2.inRange(mm_del_radio, lower_color, upper_color)  # 这是粗略的边缘掩码
    edge_mask = cv2.bitwise_and(edge_mask_rough, road_mask_cf)  # 三色差不超过1
    mm_info.road_mask_with_edge = cv2.bitwise_or(mm_info.road_mask, edge_mask)


def init_road_mask_for_sim_uni(mm_info: MiniMapInfo):
    """
    获取道路掩码 模拟宇宙专用
    不需要考虑特殊点 以及其它楼层
    :param mm_info: 小地图信息
    :return:
    """
    init_road_mask_for_world_patrol(mm_info, another_floor=False)


def get_mini_map_radio_mask(mm: MatLike, angle: float = None, another_floor: bool = True):
    """
    小地图中心雷达区的掩码
    :param mm: 小地图图片
    :param angle: 当前人物角度
    :param another_floor: 是否有其它楼层
    :return:
    """
    radio_mask = np.zeros(mm.shape[:2], dtype=np.uint8)  # 圈出雷达区的掩码
    center = (mm.shape[1] // 2, mm.shape[0] // 2)  # 中心点坐标
    radius = 55  # 扇形半径 这个半径内
    color = 255  # 扇形颜色（BGR格式）
    thickness = -1  # 扇形边框线宽度（负值表示填充扇形）
    if angle is not None:  # 知道当前角度的话 画扇形
        start_angle = angle - 45  # 扇形起始角度（以度为单位）
        end_angle = angle + 45  # 扇形结束角度（以度为单位）
        cv2.ellipse(radio_mask, center, (radius, radius), 0, start_angle, end_angle, color, thickness)  # 画扇形
    else:  # 圆形兜底
        cv2.circle(radio_mask, center, radius, color, thickness)  # 画扇形
    radio_map = cv2.bitwise_and(mm, mm, mask=radio_mask)
    # cv2_utils.show_image(radio_map, win_name='radio_map')
    # 当前层数的
    lower_color = np.array([70, 70, 45], dtype=np.uint8)
    upper_color = np.array([130, 130, 65], dtype=np.uint8)
    road_radio_mask_1 = cv2.inRange(radio_map, lower_color, upper_color)

    if another_floor:
        # 其他层数的
        lower_color = np.array([70, 70, 70], dtype=np.uint8)
        upper_color = np.array([130, 130, 85], dtype=np.uint8)
        road_radio_mask_2 = cv2.inRange(radio_map, lower_color, upper_color)

        road_radio_mask = cv2.bitwise_or(road_radio_mask_1, road_radio_mask_2)
    else:
        road_radio_mask = road_radio_mask_1

    return road_radio_mask


def merge_all_map_mask(gray_image: MatLike,
                       road_mask, sp_mask):
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
    usage[np.where(all_mask == 0)] = game_const.COLOR_WHITE_GRAY
    usage[np.where(road_mask == 255)] = game_const.COLOR_MAP_ROAD_GRAY
    return usage, all_mask


def get_edge_mask(origin: MatLike, road_mask: MatLike, another_floor: bool = False):
    """
    小地图道路边缘掩码 暂时不需要
    :param origin: 小地图图片
    :param road_mask: 道路掩码
    :param another_floor: 是否有另一层
    :return:
    """
    lower_color = np.array([170, 170, 170], dtype=np.uint8)
    upper_color = np.array([230, 230, 230], dtype=np.uint8)
    edge_mask_1 = cv2.inRange(origin, lower_color, upper_color)
    if another_floor:
        lower_color = np.array([100, 100, 100], dtype=np.uint8)
        upper_color = np.array([130, 130, 130], dtype=np.uint8)
        edge_mask_2 = cv2.inRange(origin, lower_color, upper_color)

        color_edge_mask = cv2.bitwise_or(edge_mask_1, edge_mask_2)
    else:
        color_edge_mask = edge_mask_1
    # 稍微膨胀一下
    color_edge_mask = cv2.dilate(color_edge_mask, np.ones((5, 5), np.uint8), iterations=1)

    road_edge_mask = cv2.Canny(road_mask, threshold1=200, threshold2=230)
    color_edge_mask = cv2.dilate(color_edge_mask, np.ones((2, 2), np.uint8), iterations=1)
    cv2_utils.show_image(color_edge_mask, win_name='color_edge_mask')
    cv2_utils.show_image(road_edge_mask, win_name='road_edge_mask')

    final_edge_mask = cv2.bitwise_and(color_edge_mask, road_edge_mask)

    return final_edge_mask


def find_one_enemy_pos(mm: Optional[MatLike] = None,
                       mm_del_radio: Optional[MatLike] = None) -> Optional[Point]:
    """
    在小地图上找到敌人红点的位置
    目前只能处理一个红点的情况
    :param mm: 小地图图片 与下二选一
    :param mm_del_radio: 去除雷达的小地图图片 与上二选一
    :param im: 图片匹配器
    :return: 红点位置
    """
    if mm is None and mm_del_radio is None:
        return None
    if mm_del_radio is None:
        angle = analyse_angle(mm)
        to_del = get_radio_to_del(angle)
        mm_del_radio = remove_radio(mm, to_del)

    lower_color = np.array([0, 0, 150], dtype=np.uint8)
    upper_color = np.array([60, 60, 255], dtype=np.uint8)
    red_part = cv2.inRange(mm_del_radio, lower_color, upper_color)
    # cv2_utils.show_image(red_part, win_name='red_part')

    # 膨胀一下找连通块
    to_check = cv2_utils.dilate(red_part, 5)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(to_check, connectivity=8)

    if num_labels <= 1:  # 没有连通块 走到敌人附近了
        return None

    # 找到最大的连通区域
    largest_label = 1
    max_area = stats[largest_label, cv2.CC_STAT_AREA]
    for label in range(2, num_labels):
        area = stats[label, cv2.CC_STAT_AREA]
        if area > max_area:
            max_area = area
            largest_label = label

    # 找到最大连通区域的中心点
    center_x = int(centroids[largest_label, 0])
    center_y = int(centroids[largest_label, 1])

    return Point(center_x, center_y)


def get_enemy_pos(mm_info: MiniMapInfo) -> List[Point]:
    """
    获取敌人的位置 以小地图中心为 (0,0)
    :param mm_info: 小地图信息
    :return:
    """
    enemy_mask = get_enemy_mask(mm_info)
    # cv2_utils.show_image(enemy_mask, win_name='get_enemy_pos', wait=0)
    cx = mm_info.origin.shape[1] // 2
    cy = mm_info.origin.shape[0] // 2

    # 膨胀一下找连通块
    to_check = cv2_utils.dilate(enemy_mask, 5)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(to_check, connectivity=8)

    pos_list: List[Point] = []

    if num_labels <= 1:  # 没有连通块 走到敌人附近了
        return pos_list

    # 找到最大的连通区域
    for label in range(1, num_labels):
        # 找到各个连通区域的中心点
        center_x = int(centroids[label, 0])
        center_y = int(centroids[label, 1])
        pos_list.append(Point(center_x - cx, center_y - cy))

    return pos_list


def get_closest_enemy_pos(mm_info: MiniMapInfo) -> Tuple[Point, float]:
    """
    获取最近的敌人的位置 以小地图中心为 (0,0)
    :param mm_info: 小地图信息
    :return: 无敌人时为空
    """
    pos_list = get_enemy_pos(mm_info)
    if len(pos_list) == 0:
        return None, None
    center = Point(0, 0)
    closest_dis: float = 999
    closest_pos: Optional[Point] = None

    for pos in pos_list:
        dis = cal_utils.distance_between(center, pos)
        if dis < closest_dis:
            closest_dis = dis
            closest_pos = pos

    return closest_pos, closest_dis


def with_enemy_nearby(mm_del_radio: MatLike):
    """
    判断附近是否有敌人
    :param mm_del_radio: 去除雷达的小地图图片
    :return:
    """
    center_mask = np.zeros(mm_del_radio.shape[:2], dtype=np.uint8)
    cx = mm_del_radio.shape[1] // 2
    cy = mm_del_radio.shape[0] // 2
    center_mask[cx-15:cx+15, cy-15:cy+15] = 255

    lower_color = np.array([0, 0, 150], dtype=np.uint8)
    upper_color = np.array([60, 60, 255], dtype=np.uint8)
    red_part = cv2.inRange(mm_del_radio, lower_color, upper_color)

    # 只保留中心点附近的
    red_part[:cx-15, :] = 0
    red_part[cx+15:, :] = 0
    red_part[:, :cy-15] = 0
    red_part[:, cy+15:] = 0
    # cv2_utils.show_image(red_part, win_name='red_part', wait=0)

    return np.max(red_part) > 0


def get_enemy_mask(mm_info: MiniMapInfo, with_radio: bool = False) -> MatLike:
    """
    获取敌人红点的掩码
    :param mm_info: 小地图信息
    :param with_radio: 是否包含雷达部分
    :return: 敌人红点的掩码
    """
    mm_del_radio = mm_info.origin_del_radio
    # cv2_utils.show_image(mm_del_radio, win_name='get_enemy_mask')
    b, g, r = cv2.split(mm_del_radio)
    b_g = b - g
    lower_color = np.array([45, 45, 80], dtype=np.uint8)
    if not with_radio:  # 不包含雷达的话 只取最红色的部分
        lower_color[2] = 170
    upper_color = np.array([70, 70, 255], dtype=np.uint8)
    enemy_mask_1 = cv2.inRange(mm_del_radio, lower_color, upper_color)  # 这是粗略的敌人图
    enemy_mask_2 = np.zeros(mm_del_radio.shape[:2], dtype=np.uint8)
    enemy_mask_2[(b_g <= 2) | (b_g >= -2)] = 255  # 敌人的雷达图 g 约等于 b
    enemy_mask = cv2.bitwise_and(enemy_mask_1, enemy_mask_2)

    return cv2.bitwise_and(enemy_mask, mm_info.circle_mask)


def with_enemy_nearby_new(mm_info: MiniMapInfo):
    """
    判断附近是否有敌人
    :param mm_info: 小地图信息
    :return:
    """
    enemy_pos = get_enemy_pos(mm_info)

    closest_dis = 999
    for pos in enemy_pos:
        dis = cal_utils.distance_between(Point(0, 0), pos)
        if dis < closest_dis:
            closest_dis = dis

    return closest_dis < mm_info.origin.shape[0] // 4  # 半个小地图内


def is_under_attack_new(mm_info: MiniMapInfo, danger: bool = False, enemy: bool = False) -> bool:
    """
    新的被怪锁定判断
    :param mm_info: 小地图信息
    :param danger: 红色告警 被锁定了
    :param enemy: 小地图上是否有红点在旁边
    :return:
    """
    _, g, r = cv2.split(mm_info.origin_del_radio)
    red_mask = np.zeros_like(r, dtype=np.uint8)
    if not danger:
        red_mask[r > 200] = 255
    else:
        red_mask[(r > 200) & (g < 100)] = 255
    # cv2_utils.show_image(red_mask, win_name='red_mask', wait=0)

    cx = r.shape[1] // 2

    circles = cv2.HoughCircles(red_mask, cv2.HOUGH_GRADIENT, 0.3, 100,
                               param1=10, param2=10,
                               minRadius=cx - 10, maxRadius=cx + 10)
    under = circles is not None

    if not under:
        return False
    elif enemy:
        return with_enemy_nearby_new(mm_info)
    else:
        return True

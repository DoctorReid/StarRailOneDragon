import cv2
import numpy as np
import os
from cv2.typing import MatLike
import random
from typing import List, Optional, Tuple

from one_dragon.base.geometry.point import Point
from one_dragon.base.geometry.rectangle import Rect
from one_dragon.base.matcher.match_result import MatchResult, MatchResultList
from one_dragon.base.screen.template_info import TemplateInfo
from one_dragon.utils import cv2_utils
from one_dragon.utils.log_utils import log
from sr_od.config import game_const
from sr_od.config.game_config import MiniMapPos
from sr_od.context.sr_context import SrContext
from sr_od.sr_map.large_map_info import LargeMapInfo
from sr_od.sr_map.sr_map_def import Planet, Region, SpecialPoint

CUT_MAP_RECT = Rect(200, 190, 1300, 930)  # 主区域 在屏幕上截取大地图的区域
SUB_CUT_MAP_RECT = Rect(200, 190, 1600, 955)  # 子区域 在屏幕上截取大地图的区域
EMPTY_MAP_POS = Point(1350, 800)  # 地图空白区域 用于取消选择传送点 和 拖动地图
REGION_LIST_RECT = Rect(1480, 200, 1820, 1000)
FLOOR_LIST_PART = Rect(30, 580, 110, 1000)  # 外层地图和子地图的x轴不太一样 取一个并集

LARGE_MAP_POWER_RECT = Rect(1635, 54, 1678, 72)  # 大地图上显示体力的位置
EMPTY_COLOR: int = 210  # 大地图空白地方的颜色


def get_screen_map_rect(region: Region) -> Rect:
    """
    获取区域对应的屏幕上大地图范围
    :param region: 区域
    :return:
    """
    return CUT_MAP_RECT if region.parent is None else SUB_CUT_MAP_RECT


def get_planet(ctx: SrContext, screen: MatLike) -> Optional[Planet]:
    """
    从屏幕左上方 获取当前星球的名字
    :param ctx: 上下文
    :param screen: 游戏画面
    :return: 星球名称
    """
    area = ctx.screen_loader.get_area('大地图', '星球名称')
    planet_name_part = cv2_utils.crop_image_only(screen, area.rect)
    # cv2_utils.show_image(white_part, win_name='white_part')
    planet_name_str: str = ctx.ocr.run_ocr_single_line(planet_name_part)

    return ctx.map_data.best_match_planet_by_name(planet_name_str)


def get_sp_mask_by_template_match(ctx: SrContext, lm_info: LargeMapInfo,
                                  template_type: str = 'raw',
                                  template_list: List = None,
                                  show: bool = False):
    """
    在地图中 圈出传送点、商铺点等可点击交互的的特殊点
    使用模板匹配
    :param ctx: 上下文
    :param lm_info: 大地图
    :param template_type: 模板类型
    :param template_list: 限定种类的特殊点
    :param show: 是否展示结果
    :return: 特殊点组成的掩码图 特殊点是白色255、特殊点的匹配结果
    """
    sp_match_result = {}
    source = lm_info.raw if template_type == 'raw' else lm_info.gray
    sp_mask = np.zeros(source.shape[:2], dtype=np.uint8)
    # 找出特殊点位置
    for prefix in ['mm_tp', 'mm_sp', 'mm_boss', 'mm_sub']:
        for i in range(100):
            if i == 0:
                continue
            template_id = '%s_%02d' % (prefix, i)
            if template_list is not None and template_id not in template_list:
                continue
            ti: TemplateInfo = ctx.template_loader.get_template('mm_icon', template_id)
            if ti is None:
                break
            template = ti.raw if template_type == 'raw' else ti.gray
            template_mask = ti.mask

            # print(template_id)
            match_result = cv2_utils.match_template(
                source, template, mask=template_mask,
                threshold=game_const.THRESHOLD_SP_TEMPLATE_IN_LARGE_MAP,
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


def get_active_region_name(ctx: SrContext, screen: MatLike) -> Optional[str]:
    """
    在大地图界面 获取右边列表当前选择的区域 白色字体
    :param ctx: 上下文
    :param screen: 大地图界面截图
    :return: 当前选择区域
    """
    lower = 230
    upper = 255
    part, _ = cv2_utils.crop_image(screen, REGION_LIST_RECT)
    bw = cv2.inRange(part, (lower, lower, lower), (upper, upper, upper))
    bw = cv2_utils.connection_erase(bw)
    # cv2_utils.show_image(bw, win_name='get_active_region_name_bw')
    left, right, top, bottom = cv2_utils.get_four_corner(bw)
    if left is None:
        return None
    rect = Rect(left[0] - 10, top[1] - 10, right[0] + 10, bottom[1] + 10)
    to_ocr: MatLike = cv2_utils.crop_image_only(part, rect)
    # cv2_utils.show_image(to_ocr, win_name='get_active_region_name', wait=0)
    return ctx.ocr.run_ocr_single_line(to_ocr, strict_one_line=False)


def get_active_floor(ctx: SrContext, screen: MatLike) -> Optional[str]:
    """
    在大地图界面 获取左下方当前选择的层数 黑色字体
    :param ctx: 上下文
    :param screen: 大地图界面截图
    :return: 当前选择区域
    """
    lower = 0
    upper = 90
    part, _ = cv2_utils.crop_image(screen, FLOOR_LIST_PART)
    bw = cv2.inRange(part, (lower, lower, lower), (upper, upper, upper))
    left, right, top, bottom = cv2_utils.get_four_corner(bw)
    if left is None:
        return None
    rect = Rect(left[0] - 10, top[1] - 10, right[0] + 10, bottom[1] + 10)
    to_ocr: MatLike = cv2_utils.crop_image_only(part, rect)
    # cv2_utils.show_image(to_ocr, win_name='get_active_floor', wait=0)

    return ctx.ocr.run_ocr_single_line(to_ocr)


def init_large_map(ctx: SrContext, region: Region, raw: MatLike,
                   expand_arr: List = None,
                   save: bool = False) -> LargeMapInfo:
    """
    初始化大地图需要用的数据
    :param ctx: 上下文
    :param region: 区域
    :param raw: 大地图原始图片
    :param expand_arr: 需要拓展的大小
    :param save: 是否保存
    :return:
    """
    info = LargeMapInfo()
    info.region = region
    if expand_arr is None:
        expand_arr = get_expand_arr(raw, ctx.game_config.mini_map_pos, get_screen_map_rect(region))
    info.raw = expand_raw(raw, expand_arr)
    # info.gray = cv2.cvtColor(info.origin, cv2.COLOR_BGRA2GRAY)
    sp_mask, info.sp_result = get_sp_mask_by_template_match(ctx, info)
    road_mask = get_large_map_road_mask(info.raw, sp_mask)
    info.mask = merge_all_map_mask(road_mask, sp_mask)

    if save:
        cv2_utils.show_image(info.raw, win_name='raw')
        cv2_utils.show_image(info.mask, win_name='mask')
        log.info('地图特殊点坐标')
        i: int = 0
        for k, v in info.sp_result.items():
            for vs in v:
                sp_info = (
                        '- uid: ""\n'
                        + '  cn: ""\n'
                        + f'  planet_name: "{region.planet.cn}"\n'
                        + f'  region_name: "{region.cn}"\n'
                        + f'  region_floor: {region.floor}\n'
                        + f'  template_id: "{k}"\n'
                        + f'  lm_pos: [{vs.center.x}, {vs.center.y}]\n'
                )

                print(sp_info)
                i += 1

        cv2.waitKey(0)

        ctx.map_data.save_large_map_image(info.raw, region, 'raw')
        ctx.map_data.save_large_map_image(info.mask, region, 'mask')

    return info


def get_expand_arr(raw: MatLike, mm_pos: MiniMapPos, screen_map_rect: Rect):
    """
    如果道路太贴近大地图边缘 使用小地图模板匹配的时候会匹配失败
    如果最后截图高度或宽度跟大地图圈定范围CUT_MAP_RECT一致 则choose_transport_point中两个大地图做模板匹配可能会报错
    这些情况需要拓展一下大地图
    :param raw: 大地图原图
    :param mm_pos: 小地图位置
    :param screen_map_rect: 屏幕上大地图的区域
    :return: 各个方向需要扩展的大小
    """
    # 道路掩码图
    mask: MatLike = get_large_map_road_mask(raw)

    padding = mm_pos.r + 10  # 边缘至少留一个小地图半径的空白

    # 四个方向需要拓展多少像素
    left, right, top, bottom = cv2_utils.get_four_corner(mask)
    lp = 0 if left[0] >= padding else padding - left[0]
    rp = 0 if right[0] + padding < raw.shape[1] else right[0] + padding + 1 - raw.shape[1]
    tp = 0 if top[1] >= padding else padding - top[1]
    bp = 0 if bottom[1] + padding < raw.shape[0] else bottom[1] + padding + 1 - raw.shape[0]

    # raw 尺寸至少跟CUT_MAP_RECT一致 所以只有上面没有拓展的情况要
    if tp == 0 and bp == 0 and raw.shape[0] == screen_map_rect.y2 - screen_map_rect.y1:
        tp = 5
        bp = 5
    if lp == 0 and rp == 0 and raw.shape[1] == screen_map_rect.x2 - screen_map_rect.x1:
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
                     fill_value=EMPTY_COLOR, dtype=np.uint8)
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


def merge_all_map_mask(road_mask, sp_mask):
    """
    :param road_mask:
    :param sp_mask:
    :return:
    """
    # 稍微膨胀一下
    kernel = np.ones((5, 5), np.uint8)
    expand_sp_mask = cv2.dilate(sp_mask, kernel, iterations=1)

    return cv2.bitwise_or(road_mask, expand_sp_mask)


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


def get_large_map_rect_by_pos(lm_shape, mm_shape, possible_pos: tuple = None) -> Optional[Rect]:
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
        ur = r + mr + 5  # 潜在位置半径 = 移动距离 + 小地图半径 + 5(多留一些边缘匹配)
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


def get_road_mask_for_sim_uni(map_image: MatLike, sp_mask: Optional[MatLike] = None) -> MatLike:
    """
    获取大地图的道路掩码
    提供给模拟宇宙专用 会合并了特殊点
    :param map_image: 地图图片
    :param sp_mask: 特殊点的掩码 道路掩码应该排除这部分
    :return: 道路掩码图 能走的部分是白色255
    """
    # 按道路颜色圈出 当前层的颜色
    l1 = 45
    u1 = 100
    lower_color = np.array([l1, l1, l1], dtype=np.uint8)
    upper_color = np.array([u1, u1, u1], dtype=np.uint8)
    road_mask = cv2.inRange(map_image, lower_color, upper_color)

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

    cv2_utils.show_image(real_road_mask, win_name='road_mask_sim', wait=0)

    return real_road_mask


def get_origin_for_sim_uni(origin: MatLike, sp_mask: MatLike) -> MatLike:
    """
    获取模板匹配用的大地图
    提供给模拟宇宙专用 将大地图的特殊点变成道路颜色
    :param origin: 正常的大地图
    :param sp_mask: 特殊点掩码
    :return:
    """
    sim = origin.copy()

    sim[np.where(sp_mask == 255)] = (55, 55, 55)
    cv2_utils.show_image(sim, win_name='sim', wait=0)

    return sim


def match_screen_in_large_map(ctx: SrContext, screen: MatLike, region: Region) -> Tuple[MatLike, MatchResult]:
    """
    在当前屏幕截图中扣出大地图部分，并匹配到完整大地图上获取偏移量
    :param ctx:
    :param screen: 游戏屏幕截图
    :param region: 目标区域
    :return:
    """
    screen_map_rect = get_screen_map_rect(region)
    screen_part = cv2_utils.crop_image_only(screen, screen_map_rect)
    lm_info = ctx.map_data.get_large_map_info(region)
    result: MatchResultList = cv2_utils.match_template(lm_info.raw, screen_part, 0.7)

    return screen_part, result.max


def drag_in_large_map(ctx: SrContext, dx: Optional[int] = None, dy: Optional[int] = None):
    """
    在大地图上拖动
    :param ctx:
    :param dx:
    :param dy:
    :return:
    """
    if dx is None:
        dx = 1 if random.randint(0, 1) == 1 else -1
    if dy is None:
        dy = 1 if random.randint(0, 1) == 1 else -1
    fx, fy = EMPTY_MAP_POS.tuple()
    drag_distance = -200
    tx, ty = fx + drag_distance * dx, fy + drag_distance * dy
    log.info('拖动地图 %s -> %s', (fx, fy), (tx, ty))
    ctx.controller.drag_to(end=Point(tx, ty), start=Point(fx, fy), duration=1)


def get_map_next_drag(lm_pos: Point, offset: MatchResult) -> Tuple[int, int]:
    """
    判断当前显示的部分大地图是否已经涵盖到目标点的坐标
    如果没有 则返回需要往哪个方向拖动
    :param lm_pos: 目标点在大地图上的坐标
    :param offset: 偏移量
    :return: 后续拖动方向 正代表坐标需要增加 正代表坐标需要减少
    """
    # 匹配结果矩形
    x1, y1 = offset.x, offset.y
    x2, y2 = x1 + offset.w, y1 + offset.h
    # 目标点坐标
    x, y = lm_pos.x, lm_pos.y

    dx, dy = 0, 0
    if x > x2:
        dx = 1
    elif x < x1:
        dx = -1
    if y > y2:
        dy = 1
    elif y < y1:
        dy = -1
    return dx, dy

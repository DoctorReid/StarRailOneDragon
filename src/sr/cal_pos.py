import concurrent.futures
from concurrent.futures import Future
from typing import List, Optional, Tuple

import cv2
import numpy as np
from cv2.typing import MatLike

import basic.cal_utils
from basic import cal_utils, Rect, Point
from basic.img import MatchResult, cv2_utils, MatchResultList
from basic.log_utils import log
from sr.const import map_const
from sr.image import ImageMatcher
from sr.image.sceenshot import mini_map, MiniMapInfo, LargeMapInfo, large_map
from sr.performance_recorder import record_performance

cal_pos_executor = concurrent.futures.ThreadPoolExecutor(thread_name_prefix='cal_pos')


def cal_character_pos(im: ImageMatcher,
                      lm_info: LargeMapInfo, mm_info: MiniMapInfo,
                      possible_pos: Optional[Tuple[int, int, float]] = None,
                      lm_rect: Rect = None, show: bool = False,
                      retry_without_rect: bool = True,
                      running: bool = False) -> Optional[Point]:
    """
    根据小地图 匹配大地图 判断当前的坐标
    :param im: 图片匹配器
    :param lm_info: 大地图信息
    :param mm_info: 小地图信息
    :param possible_pos: 可能位置 前两个为上一次的坐标，第三个为预估移动距离
    :param lm_rect: 大地图特定区域
    :param retry_without_rect: 失败时是否去除特定区域进行全图搜索
    :param show: 是否显示结果
    :param running: 角色是否在移动 移动时候小地图会缩小
    :return:
    """
    result: Optional[MatchResult] = None

    # 匹配结果 是缩放后的 offset 和宽高
    if mm_info.sp_result is not None and len(mm_info.sp_result) > 0:  # 有特殊点的时候 使用特殊点倒推位置
        result = cal_character_pos_by_sp_result(lm_info, mm_info, lm_rect=lm_rect, show=show)
        if result is not None and (result.template_scale > 1.3 or result.template_scale < 0.9):  # 不应该有这样的缩放 放弃这个结果
            log.debug('特殊点定位使用的缩放比例不符合预期')
            result = None
        # 倒推位置失败 说明大地图附近有多个相同类型的特殊点 这时候使用特征匹配也没用了
        # 只有极少部分情况需要使用特征匹配 所以不需要 mini_map.analyse_mini_map 中对所有情况都分析特征点
        # 特征点需要跟大地图的特征点获取方式一致 见 large_map.init_large_map
        # r2 = cal_character_pos_by_feature_match(lm_info, mm_info, lm_rect=lm_rect, show=show)
        # result = r2

    if result is None:  # 使用模板匹配 用灰度图的
        result = cal_character_pos_by_gray(im, lm_info, mm_info, lm_rect=lm_rect, running=running, show=show)
        if not is_valid_result_with_possible_pos(result, possible_pos, mm_info.angle):
            result = None

    # 上面灰度图中 道理掩码部分有些楼梯扣不出来 所以下面用两个都扣不出楼梯的掩码图来匹配
    if result is None:  # 使用模板匹配 用道路掩码的
        result = cal_character_pos_by_road_mask(im, lm_info, mm_info, lm_rect=lm_rect, running=running, show=show)
        if not is_valid_result_with_possible_pos(result, possible_pos, mm_info.angle):
            result = None
    #
    # if result is None:  # 使用模板匹配 用原图的
    #     result = cal_character_pos_by_original(im, lm_info, mm_info, lm_rect=lm_rect, running=running, show=show)

    # if result is None:
    #     result: MatchResult = cal_character_pos_by_merge_road_mask(im, lm_info, mm_info, lm_rect=lm_rect, running=running, show=show)

    # if result is None:  # 使用模板匹配 用道路掩码的
    #     result: MatchResult = cal_character_pos_by_edge_mask(im, lm_info, mm_info, lm_rect=lm_rect, running=running, show=show)

    if result is None:
        if lm_rect is not None and retry_without_rect:  # 整张大地图试试
            return cal_character_pos(lm_info, mm_info, running=running, show=show)
        else:
            return None

    offset_x = result.x
    offset_y = result.y
    scale = result.template_scale
    # 小地图缩放后中心点在大地图的位置 即人物坐标
    center_x = offset_x + result.w // 2
    center_y = offset_y + result.h // 2

    if show:
        cv2_utils.show_overlap(lm_info.origin, mm_info.origin, offset_x, offset_y, template_scale=scale, win_name='overlap')

    log.debug('计算当前坐标为 (%s, %s) 使用缩放 %.2f 置信度 %.2f', center_x, center_y, scale, result.confidence)

    return Point(center_x, center_y)


@record_performance
def cal_character_pos_by_feature_match(lm_info: LargeMapInfo, mm_info: MiniMapInfo,
                                       lm_rect: Rect = None,
                                       show: bool = False) -> MatchResult:
    """
    使用特征匹配 在大地图上匹配小地图的位置
    :param lm_info: 大地图信息
    :param mm_info: 小地图信息
    :param lm_rect: 圈定的大地图区域 传入后更准确
    :param show: 是否显示调试结果
    :return:
    """
    gray = cv2.cvtColor(mm_info.origin, cv2.COLOR_BGR2GRAY)
    gray, feature_mask = mini_map.merge_all_map_mask(gray, mm_info.road_mask, mm_info.sp_mask)
    template_mask = mm_info.road_mask
    template_kps, template_desc = cv2_utils.feature_detect_and_compute(gray, mask=template_mask)
    source_kps, source_desc = lm_info.kps, lm_info.desc

    # 筛选范围内的特征点
    if lm_rect is not None:
        kps = []
        desc = []
        for i in range(len(source_kps)):
            p: cv2.KeyPoint = source_kps[i]
            d = source_desc[i]
            if basic.cal_utils.in_rect(Point(p.pt[0], p.pt[1]), lm_rect):
                kps.append(p)
                desc.append(d)
        source_kps = kps
        source_desc = np.array(desc)

    if len(template_kps) == 0 or len(source_kps) == 0:
        return None

    source_mask = lm_info.mask

    good_matches, offset_x, offset_y, template_scale = cv2_utils.feature_match(
        source_kps, source_desc,
        template_kps, template_desc,
        source_mask)

    if show:
        source = lm_info.origin
        template = mm_info.origin
        source_with_keypoints = cv2.drawKeypoints(source, source_kps, None)
        cv2_utils.show_image(source_with_keypoints, win_name='source_with_keypoints')
        template_with_keypoints = cv2.drawKeypoints(cv2.bitwise_and(template, template, mask=template_mask), template_kps, None)
        cv2_utils.show_image(template_with_keypoints, win_name='template_with_keypoints')
        all_result = cv2.drawMatches(template, template_kps, source, source_kps, good_matches, None, flags=2)
        cv2_utils.show_image(all_result, win_name='all_match')

    if offset_x is not None:
        template_w = gray.shape[1]
        template_h = gray.shape[0]
        # 小地图缩放后的宽度和高度
        scaled_width = int(template_w * template_scale)
        scaled_height = int(template_h * template_scale)

        return MatchResult(1, offset_x, offset_y, scaled_width, scaled_height,
                           template_scale=template_scale)
    else:
        return None


@record_performance
def cal_character_pos_by_gray(im: ImageMatcher,
                              lm_info: LargeMapInfo, mm_info: MiniMapInfo,
                              lm_rect: Rect = None,
                              running: bool = False,
                              show: bool = False) -> MatchResult:
    """
    使用模板匹配 在大地图上匹配小地图的位置 会对小地图进行缩放尝试
    使用灰度图进行匹配
    :param im: 图片匹配器
    :param lm_info: 大地图信息
    :param mm_info: 小地图信息
    :param lm_rect: 圈定的大地图区域 传入后更准确
    :param running: 任务是否在跑动
    :param show: 是否显示调试结果
    :return:
    """
    source, lm_rect = cv2_utils.crop_image(lm_info.origin, lm_rect)
    source = cv2.cvtColor(source, cv2.COLOR_BGR2GRAY)
    # 使用道路掩码
    mm = mm_info.origin_del_radio
    template = cv2.cvtColor(mm_info.origin_del_radio, cv2.COLOR_BGR2GRAY)
    road_mask = mini_map.get_rough_road_mask(mm,
                                             sp_mask=mm_info.sp_mask,
                                             arrow_mask=mm_info.arrow_mask,
                                             angle=mm_info.angle,
                                             another_floor=lm_info.region.another_floor)
    road_mask = cv2_utils.dilate(road_mask, 3)  # 把白色边缘包括进来
    template_mask = cv2.bitwise_and(mm_info.circle_mask, road_mask)

    target: MatchResult = template_match_with_scale_list_parallely(im, source, template, template_mask,
                                                                   mini_map.get_mini_map_scale_list(running),
                                                                   0.3)

    if show:
        scale = target.template_scale if target is not None else 1
        template_usage = cv2_utils.scale_image(template, scale, copy=False)
        template_mask_usage = cv2_utils.scale_image(template_mask, scale, copy=False)
        cv2_utils.show_image(mm, win_name='mini_map')
        cv2_utils.show_image(source, win_name='template_match_source')
        cv2_utils.show_image(cv2.bitwise_and(template_usage, template_usage, mask=template_mask_usage), win_name='template_match_template')
        cv2_utils.show_image(template_mask, win_name='template_match_template_mask')

    if target is not None:
        offset_x = target.x + (lm_rect.x1 if lm_rect is not None else 0)
        offset_y = target.y + (lm_rect.y1 if lm_rect is not None else 0)
        return MatchResult(target.confidence, offset_x, offset_y, target.w, target.h, target.template_scale)
    else:
        return None


@record_performance
def cal_character_pos_by_original(im: ImageMatcher,
                                  lm_info: LargeMapInfo, mm_info: MiniMapInfo,
                                  lm_rect: Rect = None,
                                  running: bool = False,
                                  show: bool = False,
                                  scale_list: List[float] = None,
                                  match_threshold: float = 0.3) -> MatchResult:
    """
    使用模板匹配 在大地图上匹配小地图的位置 会对小地图进行缩放尝试
    使用小地图原图 - 需要到这一步 说明背景比较杂乱 因此道路掩码只使用中心点包含的连通块
    :param im: 图片匹配器
    :param lm_info: 大地图信息
    :param mm_info: 小地图信息
    :param lm_rect: 圈定的大地图区域 传入后更准确
    :param running: 任务是否在跑动
    :param show: 是否显示调试结果
    :param scale_list: 缩放比例
    :param match_threshold: 模板匹配的阈值
    :return:
    """
    source, lm_rect = cv2_utils.crop_image(lm_info.origin, lm_rect)
    # 使用道路掩码
    template = mm_info.origin_del_radio
    road_mask = mini_map.get_road_mask_v4(mm_info.origin_del_radio,
                                          sp_mask=mm_info.sp_mask,
                                          arrow_mask=mm_info.arrow_mask,
                                          center_mask=mm_info.center_mask
                                          )
    dilate_road_mask = cv2_utils.dilate(road_mask, 3)
    template_mask = cv2.bitwise_and(mm_info.circle_mask, dilate_road_mask)

    if scale_list is None:
        scale_list = mini_map.get_mini_map_scale_list(running)

    target: MatchResult = template_match_with_scale_list_parallely(im, source, template, template_mask,
                                                                   scale_list, match_threshold)

    if show:
        scale = target.template_scale if target is not None else 1
        template_usage = cv2_utils.scale_image(template, scale, copy=False)
        template_mask_usage = cv2_utils.scale_image(template_mask, scale, copy=False)
        cv2_utils.show_image(mm_info.origin, win_name='mini_map')
        cv2_utils.show_image(source, win_name='template_match_source')
        cv2_utils.show_image(cv2.bitwise_and(template_usage, template_usage, mask=template_mask_usage), win_name='template_match_template')
        cv2_utils.show_image(template_mask, win_name='template_match_template_mask')

    if target is not None:
        offset_x = target.x + (lm_rect.x1 if lm_rect is not None else 0)
        offset_y = target.y + (lm_rect.y1 if lm_rect is not None else 0)
        return MatchResult(target.confidence, offset_x, offset_y, target.w, target.h, target.template_scale)
    else:
        return None


@record_performance
def cal_character_pos_by_sp_result(lm_info: LargeMapInfo, mm_info: MiniMapInfo,
                                   lm_rect: Rect = None,
                                   show: bool = False) -> MatchResult:
    """
    根据特殊点 计算小地图在大地图上的位置
    :param lm_info: 大地图信息
    :param mm_info: 小地图信息
    :param lm_rect: 圈定的大地图区域 传入后更准确
    :param show: 是否显示调试结果
    :return:
    """
    mm_height, mm_width = mm_info.origin.shape[:2]

    lm_sp_map = map_const.get_sp_type_in_rect(lm_info.region, lm_rect)

    cal_pos_list = []

    for template_id, v in mm_info.sp_result.items():
        lm_sp = lm_sp_map.get(template_id) if template_id in lm_sp_map else []
        if len(lm_sp) == 0:
            continue
        for r in v:
            # 特殊点是按照大地图缩放比例获取的 因为可以反向将小地图缩放回人物静止时的大小
            mm_scale = 1 / r.template_scale
            x = r.x / r.template_scale
            y = r.y / r.template_scale
            # 特殊点中心在小地图上的位置
            cx = int(x + r.w // 2)
            cy = int(y + r.h // 2)
            scaled_width = int(mm_width / r.template_scale)
            scaled_height = int(mm_height / r.template_scale)

            # 通过大地图上相同的特殊点 反推小地图在大地图上的偏移量
            for sp in lm_sp:
                cal_x = sp.lm_pos.x - cx
                cal_y = sp.lm_pos.y - cy
                cal_pos_list.append(MatchResult(1, cal_x, cal_y, scaled_width, scaled_height, template_scale=mm_scale))

    if len(cal_pos_list) == 0:
        return None

    # 如果小地图上有个多个特殊点 则合并临近的结果 越多相同结果代表置信度越高
    merge_pos_list = []
    for pos_1 in cal_pos_list:
        merge = False
        for pos_2 in merge_pos_list:
            if cal_utils.distance_between(Point(pos_1.x, pos_1.y), Point(pos_2.x, pos_2.y)) < 10:
                merge = True
                pos_2.confidence += 1

        if not merge:
            merge_pos_list.append(pos_1)

    # 找出合并个数最多的 如果有合并个数一样的 则放弃本次结果
    target_pos = None
    same_confidence = False
    for pos in merge_pos_list:
        if target_pos is None:
            target_pos = pos
        elif pos.confidence > target_pos.confidence:
            target_pos = pos
            same_confidence = False
        elif pos.confidence == target_pos.confidence:
            same_confidence = True

    return None if same_confidence else target_pos


@record_performance
def cal_character_pos_by_road_mask(im: ImageMatcher,
                                   lm_info: LargeMapInfo, mm_info: MiniMapInfo,
                                   lm_rect: Rect = None,
                                   running: bool = False,
                                   show: bool = False,
                                   scale_list: List[float] = None) -> Optional[MatchResult]:
    """
    使用模板匹配 在大地图上匹配小地图的位置 会对小地图进行缩放尝试
    使用处理过后的道路掩码图
    :param im: 图片匹配器
    :param lm_info: 大地图信息
    :param mm_info: 小地图信息
    :param lm_rect: 圈定的大地图区域 传入后更准确
    :param running: 任务是否在跑动
    :param show: 是否显示调试结果
    :return:
    """
    source, lm_rect = cv2_utils.crop_image(lm_info.mask, lm_rect)
    # 使用道路掩码
    mm_info.road_mask = mini_map.get_road_mask_v4(mm_info.origin_del_radio,
                                                  sp_mask=mm_info.sp_mask,
                                                  arrow_mask=mm_info.arrow_mask,
                                                  center_mask=mm_info.center_mask
                                                  )
    template = mm_info.road_mask
    template_mask = mm_info.circle_mask

    if scale_list is None:
        scale_list = mini_map.get_mini_map_scale_list(running)

    target: MatchResult = template_match_with_scale_list_parallely(im, source, template, template_mask,
                                                                   scale_list,
                                                                   0.4)

    if show:
        scale = target.template_scale if target is not None else 1
        template_usage = cv2_utils.scale_image(template, scale, copy=False)
        template_mask_usage = cv2_utils.scale_image(template_mask, scale, copy=False)
        cv2_utils.show_image(mm_info.origin, win_name='mini_map')
        cv2_utils.show_image(source, win_name='template_match_source')
        cv2_utils.show_image(cv2.bitwise_and(template_usage, template_usage, mask=template_mask_usage), win_name='template_match_template')
        cv2_utils.show_image(template_mask, win_name='template_match_template_mask')

    if target is not None:
        offset_x = target.x + (lm_rect.x1 if lm_rect is not None else 0)
        offset_y = target.y + (lm_rect.y1 if lm_rect is not None else 0)
        return MatchResult(target.confidence, offset_x, offset_y, target.w, target.h, target.template_scale)
    else:
        return None


def merge_road_mask(road_mask, edge_mask):
    mask = np.full(road_mask.shape, fill_value=127, dtype=np.uint8)
    mask[np.where(road_mask > 0)] = 0
    mask[np.where(edge_mask > 0)] = 255
    return mask


def template_match_with_scale_list_parallely(im: ImageMatcher,
                                             source: MatLike, template: MatLike, template_mask: MatLike,
                                             scale_list: List[float],
                                             threshold: float) -> MatchResult:
    """
    按一定缩放比例进行模板匹配，并行处理不同的缩放比例，返回置信度最高的结果
    :param im: 图片匹配器
    :param source: 原图
    :param template: 模板图
    :param template_mask: 模板掩码
    :param scale_list: 模板的缩放比例
    :param threshold: 匹配阈值
    :return: 置信度最高的结果
    """
    future_list: List[Future] = []
    for scale in scale_list:
        future_list.append(cal_pos_executor.submit(template_match_with_scale, im,  source, template, template_mask, scale, threshold))

    target: Optional[MatchResult] = None
    for future in future_list:
        try:
            result: MatchResult = future.result(1)
            if result is not None:
                # log.debug('缩放比例 %.2f 置信度 %.2f', result.template_scale, result.confidence)
                if target is None or result.confidence > target.confidence:
                    target = result
        except concurrent.futures.TimeoutError:
            log.error('模板匹配超时', exc_info=True)

    return target


def template_match_with_scale(im: ImageMatcher,
                              source: MatLike, template: MatLike, template_mask: MatLike, scale: float,
                              threshold: float) -> MatchResult:
    """
    按一定缩放比例进行模板匹配，返回置信度最高的结果
    :param im: 图片匹配器
    :param source: 原图
    :param template: 模板图
    :param template_mask: 模板掩码
    :param scale: 模板的缩放比例
    :param threshold: 匹配阈值
    :return:
    """
    template_scale = cv2_utils.scale_image(template, scale, copy=False)
    template_mask_scale = cv2_utils.scale_image(template_mask, scale, copy=False)

    # 放大后 截取中心部分来匹配 防止放大后的图片超过了原图的范围
    template_usage = np.zeros_like(template, dtype=np.uint8)
    template_mask_usage = np.zeros_like(template_mask, dtype=np.uint8)

    height, width = template.shape[:2]
    scale_height, scale_width = template_scale.shape[:2]
    cx = scale_width // 2
    cy = scale_height // 2
    sx = cx - width // 2
    ex = sx + width
    sy = cy - width // 2
    ey = sy + height

    template_usage[:, :] = template_scale[sy:ey, sx:ex]
    template_mask_usage[:, :] = template_mask_scale[sy:ey, sx:ex]

    result: MatchResultList = im.match_image(source, template_usage, mask=template_mask_usage, threshold=threshold,
                                             only_best=True, ignore_inf=True)
    if result.max is not None:
        result.max.x -= sx
        result.max.y -= sy
        result.max.w = scale_width
        result.max.h = scale_height
        result.max.template_scale = scale

    return result.max


def sim_uni_cal_pos(
        im: ImageMatcher,
        lm_info: LargeMapInfo, mm_info: MiniMapInfo,
        possible_pos: Optional[Tuple[int, int, float]] = None,
        lm_rect: Rect = None, show: bool = False,
        running: bool = False) -> Optional[Point]:
    """
    根据小地图 匹配大地图 判断当前的坐标。模拟宇宙中使用
    :param im: 图片匹配器
    :param lm_info: 大地图信息
    :param mm_info: 小地图信息
    :param possible_pos: 可能位置 前两个为上一次的坐标，第三个为预估移动距离
    :param lm_rect: 大地图特定区域
    :param show: 是否显示结果
    :param running: 角色是否在移动 移动时候小地图会缩小
    :return:
    """
    # 匹配结果 是缩放后的 offset 和宽高
    result: Optional[MatchResult] = None

    # 模拟宇宙中不需要考虑特殊点

    if result is None:  # 使用模板匹配 用原图的
        result = sim_uni_cal_pos_by_gray(im, lm_info, mm_info, lm_rect=lm_rect, running=running, show=show)
        if not is_valid_result_with_possible_pos(result, possible_pos, mm_info.angle):
            result = None

    # 使用模板匹配 道路掩码误。报率高 仅在限定范围时可使用
    if result is None and lm_rect is not None:
        result = cal_character_pos_by_road_mask(im, lm_info, mm_info, lm_rect=lm_rect, running=running, show=show)
        if not is_valid_result_with_possible_pos(result, possible_pos, mm_info.angle):
            result = None

    if result is None:
        return None

    scale = result.template_scale
    # 小地图缩放后中心点在大地图的位置 即人物坐标
    target = result.center

    if show:
        cv2_utils.show_overlap(lm_info.origin, mm_info.origin, result.x, result.y, template_scale=scale, win_name='overlap')

    log.debug('计算当前坐标为 %s 使用缩放 %.2f 置信度 %.2f', target, scale, result.confidence)

    return target


@record_performance
def sim_uni_cal_pos_by_gray(im: ImageMatcher,
                            lm_info: LargeMapInfo, mm_info: MiniMapInfo,
                            lm_rect: Rect = None,
                            running: bool = False,
                            show: bool = False,
                            scale_list: List[float] = None,
                            match_threshold: float = 0.3) -> Optional[MatchResult]:
    """
    使用模板匹配 在大地图上匹配小地图的位置 会对小地图进行缩放尝试
    使用灰度图进行匹配 使用v4的道路掩码 适合在单层地图中使用
    :param im: 图片匹配器
    :param lm_info: 大地图信息
    :param mm_info: 小地图信息
    :param lm_rect: 圈定的大地图区域 传入后更准确
    :param running: 任务是否在跑动
    :param show: 是否显示调试结果
    :param scale_list: 缩放比例
    :param match_threshold: 模板匹配的阈值
    :return:
    """
    source, lm_rect = cv2_utils.crop_image(lm_info.origin, lm_rect)
    source = cv2.cvtColor(source, cv2.COLOR_BGR2GRAY)
    # 使用道路掩码
    mm = mm_info.origin_del_radio
    template = cv2.cvtColor(mm_info.origin_del_radio, cv2.COLOR_BGR2GRAY)
    road_mask = mini_map.get_road_mask_v4(mm,
                                          sp_mask=mm_info.sp_mask,
                                          arrow_mask=mm_info.arrow_mask,
                                          center_mask=mm_info.center_mask
                                          )
    dilate_road_mask = cv2_utils.dilate(road_mask, 10)  # 把白色边缘包括进来
    template_mask = cv2.bitwise_and(mm_info.circle_mask, dilate_road_mask)

    if scale_list is None:
        scale_list = mini_map.get_mini_map_scale_list(running)
    target: MatchResult = template_match_with_scale_list_parallely(im, source, template, template_mask, scale_list, match_threshold)

    if show:
        scale = target.template_scale if target is not None else 1
        template_usage = cv2_utils.scale_image(template, scale, copy=False)
        template_mask_usage = cv2_utils.scale_image(template_mask, scale, copy=False)
        cv2_utils.show_image(mm, win_name='mini_map')
        cv2_utils.show_image(source, win_name='template_match_source')
        cv2_utils.show_image(cv2.bitwise_and(template_usage, template_usage, mask=template_mask_usage), win_name='template_match_template')
        cv2_utils.show_image(template_mask, win_name='template_match_template_mask')

    if target is not None:
        offset_x = target.x + (lm_rect.x1 if lm_rect is not None else 0)
        offset_y = target.y + (lm_rect.y1 if lm_rect is not None else 0)
        return MatchResult(target.confidence, offset_x, offset_y, target.w, target.h, target.template_scale)
    else:
        return None


def is_valid_result_with_possible_pos(result: Optional[MatchResult],
                                      possible_pos: Optional[Tuple[int, int, float]],
                                      current_angle: Optional[float]) -> bool:
    """
    判断当前计算坐标是否合理
    :param result: 坐标结果
    :param possible_pos: 可能位置 前两个为上一次的坐标，第三个为预估移动距离
    :param current_angle: 当前人物朝向
    :return:
    """
    if result is None:
        return False
    if possible_pos is None or current_angle is None:  # 无传入时不判断
        return True

    last_pos = Point(possible_pos[0], possible_pos[1])
    move_distance = possible_pos[2]
    next_pos = result.center

    dis = cal_utils.distance_between(last_pos, next_pos)
    if dis > move_distance:
        log.info('计算坐标 %s 与 当前坐标 %s 距离较远 %.2f 舍弃', next_pos, last_pos, dis)
        return False

    next_angle = cal_utils.get_angle_by_pts(last_pos, next_pos)
    angle_delta = cal_utils.angle_delta(current_angle, next_angle)
    if abs(angle_delta) > 30:
        log.info('计算坐标 %s 的角度 %.2f 与 当前朝向 %.2f 相差较大 %.2f 舍弃',
                 next_pos, next_angle, current_angle, angle_delta)
        return False

    return True

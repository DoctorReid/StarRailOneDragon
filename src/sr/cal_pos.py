import cv2
import numpy as np

import basic.cal_utils
from basic import cal_utils
from basic.img import MatchResult, cv2_utils
from basic.log_utils import log
from sr import constants
from sr.constants.map import Region
from sr.image import ImageMatcher
from sr.image.sceenshot import mini_map, MiniMapInfo, LargeMapInfo


def cal_character_pos(im: ImageMatcher,
                      lm_info: LargeMapInfo, mm_info: MiniMapInfo,
                      lm_rect: tuple = None, show: bool = False,
                      retry_without_rect: bool = True,
                      running: bool = False):
    """
    根据小地图 匹配大地图 判断当前的坐标
    :param im: 图片匹配器
    :param lm_info: 大地图信息
    :param mm_info: 小地图信息
    :param lm_rect: 大地图特定区域
    :param retry_without_rect: 失败时是否去除特定区域进行全图搜索
    :param show: 是否显示结果
    :param running: 角色是否在移动 移动时候小地图会缩小
    :return:
    """
    log.debug("准备计算当前位置 大地图区域 %s", lm_rect)

    result: MatchResult = None

    # 匹配结果 是缩放后的 offset 和宽高
    if mm_info.sp_result is not None and len(mm_info.sp_result) > 0:  # 有特殊点的时候 使用特殊点倒推位置
        result = cal_character_pos_by_sp_result(lm_info, mm_info, lm_rect=lm_rect, show=show)
        if result is None:  # 倒推位置失败 使用特征匹配
            result = cal_character_pos_by_feature_match(lm_info, mm_info, lm_rect=lm_rect, show=show)

    if result is None:  # 使用模板匹配 用道路掩码的
        result: MatchResult = cal_character_pos_by_road_mask(im, lm_info, mm_info, lm_rect=lm_rect, running=running, show=show)

    # if result is None:
    #     result: MatchResult = cal_character_pos_by_merge_road_mask(im, lm_info, mm_info, lm_rect=lm_rect, running=running, show=show)

    # if result is None:  # 使用模板匹配 用道路掩码的
    #     result: MatchResult = cal_character_pos_by_edge_mask(im, lm_info, mm_info, lm_rect=lm_rect, running=running, show=show)

    # if result is None:  # 特征匹配失败 或者无特殊点的时候 使用模板匹配 用原图的
    #     result: MatchResult = cal_character_pos_by_template_match(im, lm_info, mm_info, lm_rect=lm_rect, running=running, show=show)

    if result is None:
        if lm_rect is not None and retry_without_rect:  # 整张大地图试试
            return cal_character_pos(lm_info, mm_info, running=running, show=show)
        else:
            return None, None

    offset_x = result.x
    offset_y = result.y
    scale = result.template_scale
    # 小地图缩放后中心点在大地图的位置 即人物坐标
    center_x = offset_x + result.w // 2
    center_y = offset_y + result.h // 2

    if show:
        cv2_utils.show_overlap(lm_info.origin, mm_info.origin, offset_x, offset_y, template_scale=scale, win_name='overlap')

    log.debug('计算当前坐标为 (%s, %s) 使用缩放 %.2f 置信度 %.2f', center_x, center_y, scale, result.confidence)

    return center_x, center_y


def cal_character_pos_by_feature_match(lm_info: LargeMapInfo, mm_info: MiniMapInfo,
                                       lm_rect: tuple = None,
                                       show: bool = False) -> MatchResult:
    """
    使用特征匹配 在大地图上匹配小地图的位置
    :param lm_info: 大地图信息
    :param mm_info: 小地图信息
    :param lm_rect: 圈定的大地图区域 传入后更准确
    :param show: 是否显示调试结果
    :return:
    """
    template_kps, template_desc = mm_info.kps, mm_info.desc
    source_kps, source_desc = lm_info.kps, lm_info.desc

    # 筛选范围内的特征点
    if lm_rect is not None:
        kps = []
        desc = []
        for i in range(len(source_kps)):
            p: cv2.KeyPoint = source_kps[i]
            d = source_desc[i]
            if basic.cal_utils.in_rect(p.pt, lm_rect):
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
        template_mask = mm_info.feature_mask
        source_with_keypoints = cv2.drawKeypoints(source, source_kps, None)
        cv2_utils.show_image(source_with_keypoints, win_name='source_with_keypoints')
        template_with_keypoints = cv2.drawKeypoints(cv2.bitwise_and(template, template, mask=template_mask), template_kps, None)
        cv2_utils.show_image(template_with_keypoints, win_name='template_with_keypoints')
        all_result = cv2.drawMatches(template, template_kps, source, source_kps, good_matches, None, flags=2)
        cv2_utils.show_image(all_result, win_name='all_match')

    if offset_x is not None:
        template_w = mm_info.gray.shape[1]
        template_h = mm_info.gray.shape[0]
        # 小地图缩放后的宽度和高度
        scaled_width = int(template_w * template_scale)
        scaled_height = int(template_h * template_scale)

        return MatchResult(1, offset_x, offset_y, scaled_width, scaled_height,
                           template_scale=template_scale)
    else:
        return None


def cal_character_pos_by_template_match(im: ImageMatcher,
                                        lm_info: LargeMapInfo, mm_info: MiniMapInfo,
                                        lm_rect: tuple = None,
                                        running: bool = False,
                                        show: bool = False) -> MatchResult:
    """
    使用模板匹配 在大地图上匹配小地图的位置 会对小地图进行缩放尝试
    使用小地图原图
    :param im: 图片匹配器
    :param lm_info: 大地图信息
    :param mm_info: 小地图信息
    :param lm_rect: 圈定的大地图区域 传入后更准确
    :param running: 任务是否在跑动
    :param show: 是否显示调试结果
    :return:
    """
    template_w = mm_info.gray.shape[1]
    template_h = mm_info.gray.shape[0]
    source, lm_rect = cv2_utils.crop_image(lm_info.origin, lm_rect)
    target: MatchResult = None
    target_scale = None
    # 使用道路掩码
    origin_template_mask = cv2_utils.dilate(mm_info.road_mask, 10)
    origin_template_mask = cv2.bitwise_and(origin_template_mask, mm_info.circle_mask)
    for scale in mini_map.get_mini_map_scale_list(running):
        if scale > 1:
            dest_size = (int(template_w * scale), int(template_h * scale))
            template = cv2.resize(mm_info.origin, dest_size)
            template_mask = cv2.resize(origin_template_mask, dest_size)
        else:
            template = mm_info.origin
            template_mask = origin_template_mask

        result = im.match_image(source, template, mask=template_mask, threshold=0.4, ignore_inf=True)

        if show:
            cv2_utils.show_image(source, win_name='template_match_source')
            cv2_utils.show_image(template, win_name='template_match_template')
            cv2_utils.show_image(template_mask, win_name='template_match_template_mask')
            # cv2_utils.show_image(cv2.bitwise_and(template, template_mask), win_name='template_match_template')
            # cv2.waitKey(0)

        if result.max is not None:
            target = result.max
            target_scale = scale
            break  # 节省点时间 其中一个缩放匹配到就可以了 也不用太精准
    if target is not None:
        offset_x = target.x + (lm_rect[0] if lm_rect is not None else 0)
        offset_y = target.y + (lm_rect[1] if lm_rect is not None else 0)
        return MatchResult(target.confidence, offset_x, offset_y, target.w, target.h, target_scale)
    else:
        return None

def cal_character_pos_by_sp_result(lm_info: LargeMapInfo, mm_info: MiniMapInfo,
                                   lm_rect: tuple = None,
                                   show: bool = False) -> MatchResult:
    """
    根据特殊点 计算小地图在大地图上的位置
    :param lm_info: 大地图信息
    :param mm_info: 小地图信息
    :param lm_rect: 圈定的大地图区域 传入后更准确
    :param show: 是否显示调试结果
    :return:
    """
    mm_height, mm_width = mm_info.gray.shape[:2]

    lm_sp_map = constants.map.get_sp_type_in_rect(lm_info.region, lm_rect)

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
                cal_x = sp.lm_pos[0] - cx
                cal_y = sp.lm_pos[1] - cy
                cal_pos_list.append(MatchResult(1, cal_x, cal_y, scaled_width, scaled_height, template_scale=mm_scale))

    if len(cal_pos_list) == 0:
        return None

    # 如果小地图上有个多个特殊点 则合并临近的结果 越多相同结果代表置信度越高
    merge_pos_list = []
    for pos_1 in cal_pos_list:
        merge = False
        for pos_2 in merge_pos_list:
            if cal_utils.distance_between((pos_1.x, pos_1.y), (pos_2.x, pos_2.y)) < 10:
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


def cal_character_pos_by_road_mask(im: ImageMatcher,
                                   lm_info: LargeMapInfo, mm_info: MiniMapInfo,
                                   lm_rect: tuple = None,
                                   running: bool = False,
                                   show: bool = False) -> MatchResult:
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
    template_w = mm_info.gray.shape[1]
    template_h = mm_info.gray.shape[0]
    source, lm_rect = cv2_utils.crop_image(lm_info.gray, lm_rect)
    target: MatchResult = None
    target_scale = None
    # 使用道路掩码
    origin_template = mm_info.gray
    origin_template_mask = mm_info.center_mask
    for scale in mini_map.get_mini_map_scale_list(running):
        if scale > 1:
            dest_size = (int(template_w * scale), int(template_h * scale))
            template = cv2.resize(origin_template, dest_size)
            template_mask = cv2.resize(origin_template_mask, dest_size)
        else:
            template = origin_template
            template_mask = origin_template_mask

        result = im.match_image(source, template, mask=template_mask, threshold=0.4, ignore_inf=True)

        if show:
            cv2_utils.show_image(mm_info.origin, win_name='mini_map')
            cv2_utils.show_image(source, win_name='template_match_source')
            cv2_utils.show_image(cv2.bitwise_and(template, template_mask), win_name='template_match_template')
            # cv2_utils.show_image(template, win_name='template_match_template')
            cv2_utils.show_image(template_mask, win_name='template_match_template_mask')
            # cv2.waitKey(0)

        if result.max is not None:
            if target is None or result.max.confidence > target.confidence:
                target = result.max
                target_scale = scale
                # break  # 节省点时间 其中一个缩放匹配到就可以了 也不用太精准
    if target is not None:
        offset_x = target.x + (lm_rect[0] if lm_rect is not None else 0)
        offset_y = target.y + (lm_rect[1] if lm_rect is not None else 0)
        return MatchResult(target.confidence, offset_x, offset_y, target.w, target.h, target_scale)
    else:
        return None


def cal_character_pos_by_merge_road_mask(im: ImageMatcher,
                                         lm_info: LargeMapInfo, mm_info: MiniMapInfo,
                                         lm_rect: tuple = None,
                                         running: bool = False,
                                         show: bool = False) -> MatchResult:
    """
    使用模板匹配 在大地图上匹配小地图的位置 会对小地图进行缩放尝试
    使用处理过后的道路灰度图
    :param im: 图片匹配器
    :param lm_info: 大地图信息
    :param mm_info: 小地图信息
    :param lm_rect: 圈定的大地图区域 传入后更准确
    :param running: 任务是否在跑动
    :param show: 是否显示调试结果
    :return:
    """
    template_w = mm_info.gray.shape[1]
    template_h = mm_info.gray.shape[0]
    source = merge_road_mask(lm_info.mask, lm_info.edge)
    source, lm_rect = cv2_utils.crop_image(source, lm_rect)
    target: MatchResult = None
    target_scale = None
    # 使用道路掩码
    origin_template = merge_road_mask(mm_info.road_mask, mm_info.edge)
    origin_template_mask = mm_info.center_mask
    for scale in mini_map.get_mini_map_scale_list(running):
        if scale > 1:
            dest_size = (int(template_w * scale), int(template_h * scale))
            template = cv2.resize(origin_template, dest_size)
            template_mask = cv2.resize(origin_template_mask, dest_size)
        else:
            template = origin_template
            template_mask = origin_template_mask

        result = im.match_image(source, template, mask=template_mask, threshold=0.4, ignore_inf=True)

        if show:
            cv2_utils.show_image(mm_info.origin, win_name='mini_map')
            cv2_utils.show_image(source, win_name='template_match_source')
            cv2_utils.show_image(cv2.bitwise_and(template, template_mask), win_name='template_match_template')
            # cv2_utils.show_image(template, win_name='template_match_template')
            cv2_utils.show_image(template_mask, win_name='template_match_template_mask')
            # cv2.waitKey(0)

        if result.max is not None:
            if target is None or result.max.confidence > target.confidence:
                target = result.max
                target_scale = scale
                # break  # 节省点时间 其中一个缩放匹配到就可以了 也不用太精准
    if target is not None:
        offset_x = target.x + (lm_rect[0] if lm_rect is not None else 0)
        offset_y = target.y + (lm_rect[1] if lm_rect is not None else 0)
        return MatchResult(target.confidence, offset_x, offset_y, target.w, target.h, target_scale)
    else:
        return None


def cal_character_pos_by_edge_mask(im: ImageMatcher,
                                   lm_info: LargeMapInfo, mm_info: MiniMapInfo,
                                   lm_rect: tuple = None,
                                   running: bool = False,
                                   show: bool = False) -> MatchResult:
    """
    使用模板匹配 在大地图上匹配小地图的位置 会对小地图进行缩放尝试
    使用边缘掩码图
    :param im: 图片匹配器
    :param lm_info: 大地图信息
    :param mm_info: 小地图信息
    :param lm_rect: 圈定的大地图区域 传入后更准确
    :param running: 任务是否在跑动
    :param show: 是否显示调试结果
    :return:
    """
    template_w = mm_info.gray.shape[1]
    template_h = mm_info.gray.shape[0]
    source, lm_rect = cv2_utils.crop_image(lm_info.edge, lm_rect)
    target: MatchResult = None
    target_scale = None
    # 使用道路掩码
    origin_template = mm_info.edge
    origin_template_mask = mm_info.center_mask
    for scale in mini_map.get_mini_map_scale_list(running):
        if scale > 1:
            dest_size = (int(template_w * scale), int(template_h * scale))
            template = cv2.resize(origin_template, dest_size)
            template_mask = cv2.resize(origin_template_mask, dest_size)
        else:
            template = origin_template
            template_mask = origin_template_mask

        result = im.match_image(source, template, mask=template_mask, threshold=0.4, ignore_inf=True)

        if show:
            cv2_utils.show_image(mm_info.origin, win_name='mini_map')
            cv2_utils.show_image(source, win_name='template_match_source')
            cv2_utils.show_image(cv2.bitwise_and(template, template_mask), win_name='template_match_template')
            # cv2_utils.show_image(template, win_name='template_match_template')
            cv2_utils.show_image(template_mask, win_name='template_match_template_mask')
            # cv2.waitKey(0)

        if result.max is not None:
            if target is None or result.max.confidence > target.confidence:
                target = result.max
                target_scale = scale
                # break  # 节省点时间 其中一个缩放匹配到就可以了 也不用太精准
    if target is not None:
        offset_x = target.x + (lm_rect[0] if lm_rect is not None else 0)
        offset_y = target.y + (lm_rect[1] if lm_rect is not None else 0)
        return MatchResult(target.confidence, offset_x, offset_y, target.w, target.h, target_scale)
    else:
        return None

def merge_road_mask(road_mask, edge_mask):
    mask = np.full(road_mask.shape, fill_value=127, dtype=np.uint8)
    mask[np.where(road_mask > 0)] = 0
    mask[np.where(edge_mask > 0)] = 255
    return mask
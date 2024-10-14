import time
from typing import Optional, List, ClassVar

import cv2
import numpy as np
from cv2.typing import MatLike

from one_dragon.base.geometry.rectangle import Rect
from one_dragon.base.matcher.match_result import MatchResult
from one_dragon.utils import cv2_utils
from one_dragon.utils.log_utils import log
from sr_od.app.sim_uni.sim_uni_challenge_config import SimUniChallengeConfig
from sr_od.app.sim_uni.sim_uni_const import match_best_bless_by_ocr, SimUniBless, SimUniBlessEnum, SimUniBlessLevel
from sr_od.context.sr_context import SrContext

# TODO 后续再把这部分加入到 screen_info
# 3个祝福的情况 每个祝福有2个框 分别是名字、命途
BLESS_3_RECT_LIST: List[List[Rect]] = [
    [Rect(390, 475, 710, 510), Rect(430, 730, 670, 760)],
    [Rect(800, 475, 1120, 510), Rect(840, 730, 1080, 760)],
    [Rect(1210, 475, 1530, 510), Rect(1250, 730, 1490, 760)],
]

# 2个祝福的情况
BLESS_2_RECT_LIST: List[List[Rect]] = [
    [Rect(600, 475, 900, 510), Rect(640, 730, 860, 760)],
    [Rect(1010, 475, 1310, 510), Rect(1050, 730, 1270, 760)],
]

# 1个祝福的情况
BLESS_1_RECT_LIST: List[List[Rect]] = [
    [Rect(800, 475, 1120, 520), Rect(840, 730, 1080, 760)],
]

# 楼层开始前祝福的情况 开拓祝福
BLESS_BEFORE_LEVEL_RECT_LIST: List[List[Rect]] = [
    [Rect(423, 475, 720, 520), Rect(463, 790, 680, 820)],
    [Rect(812, 475, 1109, 520), Rect(852, 790, 1069, 820)],
    [Rect(1200, 475, 1496, 520), Rect(1240, 790, 1456, 820)],
]


def get_bless_pos(ctx: SrContext, screen: MatLike,
                  before_level_start: bool, bless_cnt_type: int = 3) -> List[MatchResult]:
    """
    获取屏幕上的祝福的位置 整体运行大约1秒
    尝试过其他两种方法
    1. 名称和命途各一个大框，总共识别两次 0.44s + 1.26s (可能是几个黑色点导致的文本推理变多)
    2. 所有框并发地识别 但单个模型并发识别有线程安全问题 多个模型的并发识别的性能也不够高
    :param ctx: 上下文
    :param screen: 游戏画面
    :param before_level_start: 楼层开始前 开拓祝福
    :param bless_cnt_type: 祝福数量类型
    :return: MatchResult.data 中是对应的祝福 Bless
    """
    if before_level_start:
        return get_bless_pos_by_rect_list(ctx, screen, BLESS_BEFORE_LEVEL_RECT_LIST)
    else:  # 这么按顺序写 可以保证最多只识别3次祝福
        bless_3 = get_bless_pos_by_rect_list(ctx, screen, BLESS_3_RECT_LIST)
        if len(bless_3) > 0 and bless_cnt_type >= 3:
            return bless_3

        bless_2 = get_bless_pos_by_rect_list(ctx, screen, BLESS_2_RECT_LIST)
        if len(bless_2) > 0 and bless_cnt_type >= 2:
            return bless_2

        bless_1 = get_bless_pos_by_rect_list(ctx, screen, BLESS_1_RECT_LIST)
        if len(bless_1) > 0 and bless_cnt_type >= 1:
            return bless_1

    return []


def get_bless_pos_by_rect_list(ctx: SrContext, screen: MatLike, rect_list: List[List[Rect]]) -> List[MatchResult]:
    bless_list: List[MatchResult] = []

    for bless_rect_list in rect_list:
        path_part = cv2_utils.crop_image_only(screen, bless_rect_list[1])
        path_ocr = ctx.ocr.run_ocr_single_line(path_part)
        # cv2_utils.show_image(path_black_part, wait=0)
        if path_ocr is None or len(path_ocr) == 0:
            break  # 其中有一个位置识别不到就认为不是使用这些区域了 加速这里的判断

        title_part = cv2_utils.crop_image_only(screen, bless_rect_list[0])
        title_ocr = ctx.ocr.run_ocr_single_line(title_part)

        bless = match_best_bless_by_ocr(title_ocr, path_ocr)

        if bless is not None:
            log.info('识别到祝福 %s', bless)
            bless_list.append(MatchResult(1,
                                          bless_rect_list[0].x1, bless_rect_list[0].y1,
                                          bless_rect_list[0].width, bless_rect_list[0].height,
                                          data=bless))

    return bless_list


def get_bless_by_priority(bless_list: List[SimUniBless], config: Optional[SimUniChallengeConfig], can_reset: bool,
                          asc: bool) -> Optional[int]:
    """
    根据优先级选择对应的祝福
    :param bless_list: 可选的祝福列表
    :param config: 挑战配置
    :param can_reset: 当前是否可以重置
    :param asc: 升序取第一个 最高优先级
    :return: 选择祝福的下标
    """
    idx_priority: List[int] = [99 for _ in bless_list]
    cnt = 0  # 优先级

    if config is not None:
        for priority_id in config.bless_priority:
            bless = SimUniBlessEnum[priority_id]
            if bless.name.endswith('000'):  # 命途内选最高级的祝福
                for bless_level in SimUniBlessLevel:
                    for idx, opt_bless in enumerate(bless_list):
                        if opt_bless.level == bless_level and opt_bless.path == bless.value.path:
                            if idx_priority[idx] == 99:
                                idx_priority[idx] = cnt
                                cnt += 1
            else:  # 命中优先级的
                for idx, opt_bless in enumerate(bless_list):
                    if opt_bless == bless.value:
                        if idx_priority[idx] == 99:
                            idx_priority[idx] = cnt
                            cnt += 1

        if not can_reset:
            for priority_id in config.bless_priority_2:
                bless = SimUniBlessEnum[priority_id]
                if bless.name.endswith('000'):  # 命途内选最高级的祝福
                    for bless_level in SimUniBlessLevel:
                        for idx, opt_bless in enumerate(bless_list):
                            if opt_bless.level == bless_level and opt_bless.path == bless.value.path:
                                if idx_priority[idx] == 99:
                                    idx_priority[idx] = cnt
                                    cnt += 1
                else:  # 命中优先级的
                    for idx, opt_bless in enumerate(bless_list):
                        if opt_bless == bless.value:
                            if idx_priority[idx] == 99:
                                idx_priority[idx] = cnt
                                cnt += 1

    if not can_reset:
        # 优先级无法命中的情况 随便选最高级的祝福
        for bless_level in SimUniBlessLevel:
            for idx, opt_bless in enumerate(bless_list):
                if opt_bless.level == bless_level:
                    if idx_priority[idx] == 99:
                        idx_priority[idx] = cnt
                        cnt += 1

    target_idx: Optional[int] = None
    target_priority: Optional[int] = None

    for idx in range(len(bless_list)):
        if can_reset and idx_priority[idx] == 99:
            continue
        if target_idx is None or \
                (asc and target_priority > idx_priority[idx]) or \
                (not asc and target_priority < idx_priority[idx]):
            target_idx = idx
            target_priority = idx_priority[idx]

    return target_idx
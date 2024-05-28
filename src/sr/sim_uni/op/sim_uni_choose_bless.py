import time
from typing import Optional, List, ClassVar

import cv2
import numpy as np
from cv2.typing import MatLike

from basic import Rect, str_utils, Point
from basic.i18_utils import gt
from basic.img import MatchResult, cv2_utils
from basic.log_utils import log
from sr.context import Context
from sr.image.ocr_matcher import OcrMatcher
from sr.image.sceenshot import screen_state
from sr.operation import Operation, OperationOneRoundResult, StateOperation, StateOperationNode, StateOperationEdge
from sr.operation.unit.click import ClickDialogConfirm
from sr.sim_uni.sim_uni_challenge_config import SimUniChallengeConfig
from sr.sim_uni.sim_uni_const import match_best_bless_by_ocr, SimUniBless, SimUniBlessEnum, SimUniBlessLevel

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


def get_bless_pos(screen: MatLike, ocr: OcrMatcher,
                  before_level_start: bool, bless_cnt_type: int = 3) -> List[MatchResult]:
    """
    获取屏幕上的祝福的位置 整体运行大约1秒
    尝试过其他两种方法
    1. 名称和命途各一个大框，总共识别两次 0.44s + 1.26s (可能是几个黑色点导致的文本推理变多)
    2. 所有框并发地识别 但单个模型并发识别有线程安全问题 多个模型的并发识别的性能也不够高
    :param screen: 屏幕截图
    :param ocr: OCR
    :param before_level_start: 楼层开始前 开拓祝福
    :param bless_cnt_type: 祝福数量类型
    :return: MatchResult.data 中是对应的祝福 Bless
    """
    if before_level_start:
        return get_bless_pos_by_rect_list(screen, ocr, BLESS_BEFORE_LEVEL_RECT_LIST)
    else:  # 这么按顺序写 可以保证最多只识别3次祝福
        bless_3 = get_bless_pos_by_rect_list(screen, ocr, BLESS_3_RECT_LIST)
        if len(bless_3) > 0 and bless_cnt_type >= 3:
            return bless_3

        bless_2 = get_bless_pos_by_rect_list(screen, ocr, BLESS_2_RECT_LIST)
        if len(bless_2) > 0 and bless_cnt_type >= 2:
            return bless_2

        bless_1 = get_bless_pos_by_rect_list(screen, ocr, BLESS_1_RECT_LIST)
        if len(bless_1) > 0 and bless_cnt_type >= 1:
            return bless_1

    return []


def get_bless_pos_by_rect_list(screen: MatLike,
                               ocr: OcrMatcher,
                               rect_list: List[List[Rect]]) -> List[MatchResult]:
    bless_list: List[MatchResult] = []

    for bless_rect_list in rect_list:
        path_part = cv2_utils.crop_image_only(screen, bless_rect_list[1])
        path_ocr = ocr.ocr_for_single_line(path_part)
        # cv2_utils.show_image(path_black_part, wait=0)
        if path_ocr is None or len(path_ocr) == 0:
            break  # 其中有一个位置识别不到就认为不是使用这些区域了 加速这里的判断

        title_part = cv2_utils.crop_image_only(screen, bless_rect_list[0])
        title_ocr = ocr.ocr_for_single_line(title_part)

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


class SimUniChooseBless(StateOperation):

    RESET_BTN: ClassVar[Rect] = Rect(1160, 960, 1460, 1000)  # 重置祝福
    CONFIRM_BTN: ClassVar[Rect] = Rect(1530, 960, 1865, 1000)  # 确认
    CONFIRM_BEFORE_LEVEL_BTN: ClassVar[Rect] = Rect(783, 953, 1133, 997)  # 确认 - 楼层开始前

    STATUS_STILL_BLESS: ClassVar[str] = '仍在选择祝福'

    def __init__(self, ctx: Context,
                 config: Optional[SimUniChallengeConfig] = None,
                 skip_first_screen_check: bool = True,
                 before_level_start: bool = False,
                 fast_back_to_world: bool = False):
        """
        按照优先级选择祝福 如果选择后仍然在选择祝福画面 则继续选择。可能的情况有
        - 连续祝福，例如第一场战斗有两次祝福
        - 脚本并没有选择到祝福，游戏画面一直停流

        选择祝福后 如果还有再次触发的内容，左上角title会较快消失。返回大世界的话，左上角title会较慢消失。
        :param ctx:
        :param config: 挑战配置
        :param skip_first_screen_check: 是否跳过第一次的画面状态检查
        :param before_level_start: 是否在楼层开始的选择
        :param fast_back_to_world 需要快速判断返回世界
        """
        edges: List[StateOperationEdge] = []

        first_wait = StateOperationNode('等待画面', self._first_wait)
        choose = StateOperationNode('选择祝福', self._choose)
        edges.append(StateOperationEdge(first_wait, choose))

        after_wait = StateOperationNode('选择后等待结束', self._wait_not_in_bless)
        edges.append(StateOperationEdge(choose, after_wait))

        super().__init__(ctx, try_times=5,
                         op_name='%s %s' % (gt('模拟宇宙', 'ui'), gt('选择祝福', 'ui')),
                         edges=edges)

        self.config: Optional[SimUniChallengeConfig] = ctx.sim_uni_challenge_config if config is None else config  # 祝福优先级
        self.skip_first_screen_check: bool = skip_first_screen_check  # 是否跳过第一次的画面状态检查 用于提速
        self.before_level_start: bool = before_level_start  # 在真正楼层开始前 即选择开拓祝福时
        self.fast_back_to_world: bool = fast_back_to_world  # 需要快速判断返回世界

    def _init_before_execute(self):
        super()._init_before_execute()
        self.first_screen_check = True
        self.choose_bless_time: Optional[float] = None  # 选择祝福的时间
        self.last_bless_pos_list: List[MatchResult] = []  # 上一次识别到的祝福
        self.bless_cnt_type: int = 3  # 祝福数量

    def _first_wait(self):
        screen = self.screenshot()

        if not self.first_screen_check or not self.skip_first_screen_check:
            self.first_screen_check = False
            if not screen_state.in_sim_uni_choose_bless(screen, self.ctx.ocr):
                return self.round_retry('未在模拟宇宙-选择祝福页面', wait=1)

        return self.round_success()

    def _choose(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        bless_pos_list: List[MatchResult] = get_bless_pos(screen, self.ctx.ocr, self.before_level_start, self.bless_cnt_type)

        if len(bless_pos_list) == 0:
            return self.round_retry('未识别到祝福', wait=1)

        if self._same_as_last(bless_pos_list):
            if self.bless_cnt_type <= 0:
                return self.round_fail('祝福与之前识别一致')
            else:
                return self.round_retry('祝福与之前识别一致', wait=1)

        self.last_bless_pos_list = bless_pos_list

        target_bless_pos: Optional[MatchResult] = self._get_bless_to_choose(screen, bless_pos_list)
        if target_bless_pos is None:
            self.ctx.controller.click(SimUniChooseBless.RESET_BTN.center)
            return self.round_wait('重置祝福', wait=1)
        else:
            self.ctx.controller.click(target_bless_pos.center)
            time.sleep(0.25)
            if self.before_level_start:
                confirm_point = SimUniChooseBless.CONFIRM_BEFORE_LEVEL_BTN.center
            else:
                confirm_point = SimUniChooseBless.CONFIRM_BTN.center
            self.ctx.controller.click(confirm_point)
            self.choose_bless_time = time.time()
            return self.round_success(wait=0.1)

    def _same_as_last(self, bless_pos_list: List[MatchResult]) -> bool:
        """
        识别的祝福内容是否跟上一次一致
        正常情况下基本不可能，只可能是识别错了，一直没有选择到祝福
        例如：
        只有2个祝福的时候，使用3个祝福的第1个位置 可能会识别到祝福(名字位置重叠) 这时候点击第1个位置是会失败的
        所以每次出现一致 bless_cnt_type-=1 即重试的时候 需要排除调3个祝福的位置 尝试2个祝福的位置
        :param bless_pos_list:
        :return: 是否一致
        """
        same: bool = True
        if len(self.last_bless_pos_list) != len(bless_pos_list):
            same = False
        else:
            for i in range(len(self.last_bless_pos_list)):
                b1: SimUniBless = self.last_bless_pos_list[i].data
                b2: SimUniBless = bless_pos_list[i].data
                if b1 != b2:
                    same = False

        if same:
            self.bless_cnt_type -= 1
        else:
            self.bless_cnt_type = 3

        return same

    def _can_reset(self, screen: MatLike) -> bool:
        """
        判断当前是否能重置
        :param screen: 屏幕祝福
        :return:
        """
        part, _ = cv2_utils.crop_image(screen, SimUniChooseBless.RESET_BTN)
        lower_color = np.array([220, 220, 220], dtype=np.uint8)
        upper_color = np.array([255, 255, 255], dtype=np.uint8)
        white_part = cv2.inRange(part, lower_color, upper_color)

        ocr_result = self.ctx.ocr.ocr_for_single_line(white_part)

        return str_utils.find_by_lcs(gt('重置祝福', 'ocr'), ocr_result)

    def _get_bless_to_choose(self, screen: MatLike, bless_pos_list: List[MatchResult]) -> Optional[MatchResult]:
        """
        根据优先级选择对应的祝福
        :param bless_pos_list: 祝福列表
        :return:
        """
        bless_list = [bless.data for bless in bless_pos_list]
        can_reset = self._can_reset(screen)
        target_idx = get_bless_by_priority(bless_list, self.config, can_reset, asc=True)
        if target_idx is None:
            return None
        else:
            return bless_pos_list[target_idx]

    def _wait_not_in_bless(self) -> OperationOneRoundResult:
        """
        选择祝福后 等待画面不是【选择祝福】再退出
        这样方便后续指令在选择祝福后立刻做其它事情
        一段时间后还在选择祝福的话 可能是连续祝福 仍然返回
        :return:
        """
        if self.fast_back_to_world:
            now = time.time()
            screen = self.screenshot()
            if screen_state.in_sim_uni_choose_bless(screen, self.ctx.ocr):

                # OCR需要时间 这里就不等待了
                if now - self.choose_bless_time >= 2:
                    return self.round_success(status=SimUniChooseBless.STATUS_STILL_BLESS)
                else:
                    return self.round_wait(status=SimUniChooseBless.STATUS_STILL_BLESS)
            else:
                return self.round_success()
        else:
            return self.round_success(wait=1)


class SimUniDropBless(StateOperation):

    STATUS_RETRY: ClassVar[str] = '重试其他祝福位置'

    def __init__(self, ctx: Context,
                 config: Optional[SimUniChallengeConfig] = None,
                 skip_first_screen_check: bool = True
                 ):
        """
        按照优先级选择祝福
        :param ctx:
        :param config: 挑战配置
        :param skip_first_screen_check: 是否跳过第一次的画面状态检查
        """
        state = StateOperationNode('画面检测', self._check_screen_state)
        choose_bless = StateOperationNode('选择祝福', self._choose_bless)
        confirm = StateOperationNode('确认', self._confirm)

        super().__init__(ctx, try_times=5,
                         op_name='%s %s' % (gt('模拟宇宙', 'ui'), gt('丢弃祝福', 'ui')),
                         nodes=[state, choose_bless, confirm])

        self.config: Optional[SimUniChallengeConfig] = config
        self.skip_first_screen_check: bool = skip_first_screen_check  # 是否跳过第一次的画面状态检查 用于提速

    def _init_before_execute(self):
        super()._init_before_execute()
        self.first_screen_check = True  # 是否第一次检查画面状态
        self.bless_cnt_type: int = 3  # 祝福数量类型

    def _check_screen_state(self):
        screen = self.screenshot()

        if self.first_screen_check and self.skip_first_screen_check:
            self.first_screen_check = False
            return self.round_success(screen_state.ScreenState.SIM_DROP_CURIOS.value)

        state = screen_state.get_sim_uni_screen_state(screen, self.ctx.im, self.ctx.ocr,
                                                      drop_bless=True)

        if state is not None:
            return self.round_success(state)
        else:
            return self.round_retry('未在丢弃祝福页面', wait=1)

    def _choose_bless(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        bless_pos_list: List[MatchResult] = get_bless_pos(screen, self.ctx.ocr, False, self.bless_cnt_type)
        if len(bless_pos_list) == 0:
            return self.round_retry('未识别到祝福', wait=1)

        bless_list = [bless.data for bless in bless_pos_list]
        target_idx: int = get_bless_by_priority(bless_list, self.config, can_reset=False, asc=False)
        self.ctx.controller.click(bless_pos_list[target_idx].center)
        time.sleep(0.25)
        self.ctx.controller.click(SimUniChooseBless.CONFIRM_BTN.center)
        return self.round_success(wait=1)

    def _confirm(self) -> OperationOneRoundResult:
        """
        确认丢弃
        :return:
        """
        op = ClickDialogConfirm(self.ctx, wait_after_success=1)
        op_result = op.execute()
        if op_result.success:
            return self.round_success()
        else:
            self.bless_cnt_type -= 1
            if self.bless_cnt_type > 0:
                return self.round_success(status=SimUniDropBless.STATUS_RETRY)
            else:
                return self.round_fail_by_op(op_result)


class SimUniUpgradeBless(StateOperation):

    UPGRADE_BTN: ClassVar[Rect] = Rect(1566, 960, 1862, 1011)  # 强化
    EXIT_BTN: ClassVar[Rect] = Rect(1829, 40, 1898, 95)  # 退出
    BLESS_RECT: ClassVar[Rect] = Rect(60, 216, 1368, 955)  # 所有祝福的框
    LEFT_RECT: ClassVar[Rect] = Rect(1680, 50, 1770, 80)  # 剩余碎片的数字

    STATUS_UPGRADE: ClassVar[str] = '强化成功'
    STATUS_NO_UPGRADE: ClassVar[str] = '无法强化'

    def __init__(self, ctx: Context):
        """
        模拟宇宙 强化祝福
        :param ctx:
        """
        edges = []

        check_left = StateOperationNode('识别剩余碎片', self._check_left)
        check_upgrade = StateOperationNode('识别可升级祝福', self._check_can_upgrade)
        edges.append(StateOperationEdge(check_left, check_upgrade))

        choose = StateOperationNode('选择祝福', self._choose_bless)
        edges.append(StateOperationEdge(check_upgrade, choose))

        upgrade = StateOperationNode('升级', self._upgrade)
        edges.append(StateOperationEdge(choose, upgrade, status=SimUniUpgradeBless.STATUS_UPGRADE))

        empty = StateOperationNode('点击空白', self._click_empty)
        edges.append(StateOperationEdge(upgrade, empty, status=SimUniUpgradeBless.STATUS_UPGRADE))
        edges.append(StateOperationEdge(empty, choose, status=SimUniUpgradeBless.STATUS_UPGRADE))

        esc = StateOperationNode('退出', self._exit)
        edges.append(StateOperationEdge(upgrade, esc, status=SimUniUpgradeBless.STATUS_NO_UPGRADE))
        edges.append(StateOperationEdge(upgrade, esc, status=SimUniUpgradeBless.STATUS_NO_UPGRADE))
        edges.append(StateOperationEdge(choose, esc, status=SimUniUpgradeBless.STATUS_NO_UPGRADE))

        super().__init__(ctx, try_times=10,
                         op_name='%s %s' % (gt('模拟宇宙', 'ui'), gt('强化祝福', 'ui')),
                         edges=edges,
                         specified_start_node=check_left
                         )

        self.left_num: int = 0  # 剩余碎片数量
        self.upgrade_list: List[MatchResult] = []  # 可升级的祝福的点击位置
        self.upgrade_idx: int = 0  # 当前需要升级的祝福下标

    def _check_left(self) -> OperationOneRoundResult:
        """
        识别剩余的碎片数量
        :return:
        """
        screen = self.screenshot()

        state = screen_state.get_sim_uni_screen_state(screen, self.ctx.im, self.ctx.ocr,
                                                      upgrade_bless=True)

        if state != screen_state.ScreenState.SIM_UPGRADE_BLESS.value:
            return self.round_retry('未在祝福强化页面', wait=1)

        num = self._get_left_num(screen)
        if num is None:
            return self.round_retry('识别剩余碎片失败', wait=1)
        else:
            self.left_num = num
            return self.round_success()

    def _get_left_num(self, screen: MatLike) -> Optional[int]:
        """
        识别剩余的碎片数量
        :return:
        """
        part = cv2_utils.crop_image_only(screen, SimUniUpgradeBless.LEFT_RECT)
        digit_str = self.ctx.ocr.ocr_for_single_line(part)
        return str_utils.get_positive_digits(digit_str, err=None)

    def _check_can_upgrade(self) -> OperationOneRoundResult:
        """
        识别可升级的祝福 按剩余碎片数量保留
        :return:
        """
        screen = self.screenshot()
        self._get_bless_pos_list(screen)

        return self.round_success()

    def _get_bless_pos_list(self, screen: MatLike) -> None:
        """
        获取一个可以强化的祝福位置
        :param screen: 屏幕截图
        :return: 可强化的祝福列表 每个元素对应碎片数量的识别结果 MatchResult.data=升级祝福需要的碎片
        """
        part = cv2_utils.crop_image_only(screen, SimUniUpgradeBless.BLESS_RECT)
        money_icon_mrl = self.ctx.im.match_template(part, 'store_money', template_sub_dir='sim_uni',
                                                    ignore_template_mask=True,   threshold=0.65, only_best=False)

        total_num: int = 0  # 当前累计使用的碎片数量
        # cv2_utils.show_image(part, money_icon_mrl, win_name='all')
        for mr in money_icon_mrl:
            lt = SimUniUpgradeBless.BLESS_RECT.left_top + mr.center + Point(15, -15)
            rb = SimUniUpgradeBless.BLESS_RECT.left_top + mr.center + Point(65, 12)
            digit_rect = Rect(lt.x, lt.y, rb.x, rb.y)
            digit_part = cv2_utils.crop_image_only(screen, digit_rect)
            white_part = cv2_utils.get_white_part(digit_part)
            # cv2_utils.show_image(white_part, win_name='digit_part', wait=0)
            ocr_result = self.ctx.ocr.ocr_for_single_line(white_part)
            digit = str_utils.get_positive_digits(ocr_result, 0)
            if digit == 0:
                continue
            if total_num + digit > self.left_num:
                continue
            total_num += digit
            self.upgrade_list.append(MatchResult(1, digit_rect.x1, digit_rect.x2, digit_rect.width, digit_rect.height,
                                                 data=digit))
            if total_num + 100 > self.left_num:  # 比较粗糙认为最少要100才能强化
                break

    def _choose_bless(self) -> OperationOneRoundResult:
        """
        选择一个祝福
        :return:
        """
        if self.upgrade_idx >= len(self.upgrade_list):
            return self.round_success(SimUniUpgradeBless.STATUS_NO_UPGRADE)

        screen = self.screenshot()

        state = screen_state.get_sim_uni_screen_state(screen, self.ctx.im, self.ctx.ocr,
                                                      upgrade_bless=True)

        if state != screen_state.ScreenState.SIM_UPGRADE_BLESS.value:
            return self.round_retry('未在祝福强化页面', wait=1)

        self.ctx.controller.click(self.upgrade_list[self.upgrade_idx].center)
        self.upgrade_idx += 1
        return self.round_success(SimUniUpgradeBless.STATUS_UPGRADE, wait=0.2)

    def _upgrade(self) -> OperationOneRoundResult:
        """
        升级
        :return:
        """
        screen = self.screenshot()

        if self._can_upgrade(screen):
            click = self.ctx.controller.click(SimUniUpgradeBless.UPGRADE_BTN.center)
            if click:
                return self.round_success(SimUniUpgradeBless.STATUS_UPGRADE, wait=2)
            else:
                return self.round_retry('点击强化失败')
        else:
            return self.round_success(SimUniUpgradeBless.STATUS_NO_UPGRADE)

    def _can_upgrade(self, screen: MatLike) -> bool:
        part = cv2_utils.crop_image_only(screen, SimUniUpgradeBless.UPGRADE_BTN)
        white = cv2_utils.get_white_part(part)
        ocr_result = self.ctx.ocr.ocr_for_single_line(white)

        return str_utils.find_by_lcs(gt('强化', 'ocr'), ocr_result, percent=0.1)

    def _click_empty(self) -> OperationOneRoundResult:
        """
        点击空白继续
        :return:
        """
        screen = self.screenshot()
        state = screen_state.get_sim_uni_screen_state(screen, self.ctx.im, self.ctx.ocr,
                                                      upgrade_bless=True,
                                                      empty_to_close=True)

        if state == screen_state.ScreenState.SIM_UPGRADE_BLESS.value:
            return self.round_success(SimUniUpgradeBless.STATUS_NO_UPGRADE)
        else:
            self.ctx.controller.click(screen_state.TargetRect.EMPTY_TO_CLOSE.value.center)
            return self.round_success(SimUniUpgradeBless.STATUS_UPGRADE, wait=1)

    def _exit(self) -> OperationOneRoundResult:
        """
        退出强化页面
        :return:
        """
        click = self.ctx.controller.click(SimUniUpgradeBless.EXIT_BTN.center)
        if click:
            return self.round_success(wait=1)
        else:
            return self.round_retry('退出失败')

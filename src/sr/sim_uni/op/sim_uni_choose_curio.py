import time
from typing import Optional, ClassVar, List

from cv2.typing import MatLike

from basic import Rect
from basic.i18_utils import gt
from basic.img import MatchResult, cv2_utils
from basic.log_utils import log
from sr.context import Context
from sr.image.sceenshot import screen_state
from sr.operation import Operation, OperationOneRoundResult, StateOperation, StateOperationNode, StateOperationEdge
from sr.operation.unit.click import ClickDialogConfirm
from sr.sim_uni.sim_uni_challenge_config import SimUniChallengeConfig
from sr.sim_uni.sim_uni_const import match_best_curio_by_ocr, SimUniCurio, SimUniCurioEnum


class SimUniChooseCurio(StateOperation):
    # 奇物名字对应的框 - 3个的情况
    CURIO_RECT_3_LIST: ClassVar[List[Rect]] = [
        Rect(315, 280, 665, 320),
        Rect(780, 280, 1120, 320),
        Rect(1255, 280, 1590, 320),
    ]

    # 奇物名字对应的框 - 2个的情况
    CURIO_RECT_2_LIST: ClassVar[List[Rect]] = [
        Rect(513, 280, 876, 320),
        Rect(1024, 280, 1363, 320),
    ]

    # 奇物名字对应的框 - 1个的情况
    CURIO_RECT_1_LIST: ClassVar[List[Rect]] = [
        Rect(780, 280, 1120, 320),
    ]

    CURIO_NAME_RECT: ClassVar[Rect] = Rect(315, 280, 1590, 320)  # 奇物名字的框

    CONFIRM_BTN: ClassVar[Rect] = Rect(1500, 950, 1840, 1000)  # 确认选择

    def __init__(self, ctx: Context, config: Optional[SimUniChallengeConfig] = None,
                 skip_first_screen_check: bool = True):
        """
        模拟宇宙中 选择奇物
        :param ctx:
        :param config: 挑战配置
        :param skip_first_screen_check: 是否跳过第一次画面状态检查
        """
        edges = []

        choose_curio = StateOperationNode('选择奇物', self._choose_curio)
        check_screen_state = StateOperationNode('游戏画面', self._check_after_confirm)
        edges.append(StateOperationEdge(choose_curio, check_screen_state))

        empty_to_continue = StateOperationNode('点击空白处关闭', self._click_empty_to_continue)
        edges.append(StateOperationEdge(check_screen_state, empty_to_continue,
                                        status='点击空白处关闭'))
        edges.append(StateOperationEdge(empty_to_continue, check_screen_state))

        super().__init__(ctx, try_times=5,
                         op_name='%s %s' % (gt('模拟宇宙', 'ui'), gt('选择奇物', 'ui')),
                         edges=edges,
                         specified_start_node=choose_curio,
                         # specified_start_node=check_screen_state,
                         )

        self.config: Optional[SimUniChallengeConfig] = config
        self.skip_first_screen_check: bool = skip_first_screen_check  # 是否跳过第一次的画面状态检查 用于提速
        self.first_screen_check: bool = True  # 是否第一次检查画面状态

    def _init_before_execute(self):
        super()._init_before_execute()
        self.first_screen_check = True

    def _choose_curio(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        if not self.first_screen_check or not self.skip_first_screen_check:
            self.first_screen_check = False
            if not screen_state.in_sim_uni_choose_curio(screen, self.ctx.ocr):
                return Operation.round_retry('未在模拟宇宙-选择奇物页面')

        curio_pos_list: List[MatchResult] = self._get_curio_pos(screen)
        if len(curio_pos_list) == 0:
            return Operation.round_retry('未识别到奇物', wait=1)

        target_curio_pos: Optional[MatchResult] = self._get_curio_to_choose(curio_pos_list)
        self.ctx.controller.click(target_curio_pos.center)
        time.sleep(0.25)
        self.ctx.controller.click(SimUniChooseCurio.CONFIRM_BTN.center)
        return Operation.round_success(wait=2)

    def _get_curio_pos(self, screen: MatLike) -> List[MatchResult]:
        """
        获取屏幕上的奇物的位置
        :param screen: 屏幕截图
        :return: MatchResult.data 中是对应的奇物 SimUniCurio
        """
        curio_list = self._get_curio_pos_by_rect(screen, SimUniChooseCurio.CURIO_RECT_3_LIST)
        if len(curio_list) > 0:
            return curio_list

        curio_list = self._get_curio_pos_by_rect(screen, SimUniChooseCurio.CURIO_RECT_2_LIST)
        if len(curio_list) > 0:
            return curio_list

        curio_list = self._get_curio_pos_by_rect(screen, SimUniChooseCurio.CURIO_RECT_1_LIST)
        if len(curio_list) > 0:
            return curio_list

        return []

    def _get_curio_pos_2(self, screen: MatLike) -> List[MatchResult]:
        """
        获取屏幕上的奇物的位置
        :param screen: 屏幕截图
        :return: MatchResult.data 中是对应的奇物 SimUniCurio
        """
        curio_list: List[MatchResult] = []
        part = cv2_utils.crop_image_only(screen, SimUniChooseCurio.CURIO_NAME_RECT)
        ocr_result_map = self.ctx.ocr.run_ocr(part)
        for title_ocr, mrl in ocr_result_map.items():
            curio = match_best_curio_by_ocr(title_ocr)

            if curio is None:  # 有一个识别不到就返回 提速
                continue

            for mr in mrl:
                mr.data = curio
                mr.x += SimUniChooseCurio.CURIO_NAME_RECT.x1
                mr.y += SimUniChooseCurio.CURIO_NAME_RECT.y1
                curio_list.append(mr)

        return curio_list

    def _get_curio_pos_by_rect(self, screen: MatLike, rect_list: List[Rect]) -> List[MatchResult]:
        """
        获取屏幕上的奇物的位置
        :param screen: 屏幕截图
        :param rect_list: 指定区域
        :return: MatchResult.data 中是对应的奇物 SimUniCurio
        """
        curio_list: List[MatchResult] = []

        for rect in rect_list:
            title_part = cv2_utils.crop_image_only(screen, rect)
            title_ocr = self.ctx.ocr.ocr_for_single_line(title_part)
            # cv2_utils.show_image(title_part, wait=0)

            curio = match_best_curio_by_ocr(title_ocr)

            if curio is None:  # 有一个识别不到就返回 提速
                return curio_list

            log.info('识别到奇物 %s', curio)
            curio_list.append(MatchResult(1,
                                          rect.x1, rect.y1,
                                          rect.width, rect.height,
                                          data=curio))

        return curio_list

    def _get_curio_to_choose(self, curio_pos_list: List[MatchResult]) -> Optional[MatchResult]:
        """
        根据优先级选择对应的奇物
        :param curio_pos_list: 奇物列表
        :return:
        """
        curio_list = [curio.data for curio in curio_pos_list]
        target_idx = SimUniChooseCurio.get_curio_by_priority(curio_list, self.config)
        if target_idx is None:
            return None
        else:
            return curio_pos_list[target_idx]

    @staticmethod
    def get_curio_by_priority(curio_list: List[SimUniCurio], config: Optional[SimUniChallengeConfig]) -> Optional[int]:
        """
        根据优先级选择对应的奇物
        :param curio_list: 可选的奇物列表
        :param config: 挑战配置
        :return: 选择的下标
        """
        if config is None:
            return 0

        for curio_id in config.curio_priority:
            curio_enum = SimUniCurioEnum[curio_id]
            for idx, opt_curio in enumerate(curio_list):
                if curio_enum.value == opt_curio:
                    return idx

        return 0

    def _check_after_confirm(self) -> OperationOneRoundResult:
        """
        确认后判断下一步动作
        :return:
        """
        screen = self.screenshot()
        state = self._get_screen_state(screen)
        if state is None:
            # 未知情况都先点击一下
            self.ctx.controller.click(screen_state.TargetRect.EMPTY_TO_CLOSE.value.center)
            return Operation.round_retry('未能判断当前页面', wait=1)
        else:
            return Operation.round_success(state)

    def _get_screen_state(self, screen: MatLike) -> Optional[str]:
        state = screen_state.get_sim_uni_screen_state(screen, self.ctx.im, self.ctx.ocr,
                                                      in_world=True,
                                                      empty_to_close=True,
                                                      bless=True,
                                                      curio=True)
        log.info('当前画面状态 %s', state)
        return state

    def _click_empty_to_continue(self) -> OperationOneRoundResult:
        click = self.ctx.controller.click(screen_state.TargetRect.EMPTY_TO_CLOSE.value.center)

        if click:
            return Operation.round_success(wait=2)
        else:
            return Operation.round_retry('点击空白处关闭失败')


class SimUniDropCurio(StateOperation):

    DROP_BTN: ClassVar[Rect] = Rect(1024, 647, 1329, 698)  # 确认丢弃
    STATUS_RETRY: ClassVar[str] = '重试其他奇物位置'

    def __init__(self, ctx: Context, config: Optional[SimUniChallengeConfig] = None,
                 skip_first_screen_check: bool = True):
        """
        模拟宇宙中 丢弃奇物
        :param ctx:
        :param config: 挑战配置
        :param skip_first_screen_check: 是否跳过第一次画面状态检查
        """
        edges: List[StateOperationEdge] = []

        state = StateOperationNode('画面检测', self._check_screen_state)
        choose_curio = StateOperationNode('选择奇物', self._choose_curio)
        edges.append(StateOperationEdge(state, choose_curio))

        confirm = StateOperationNode('确认', self._confirm)
        edges.append(StateOperationEdge(choose_curio, confirm))
        # 只有2个奇物的使用，使用3个奇物的第1个位置 可能会识别到奇物 这时候点击第1个位置是会失败的
        # 所以每次重试 curio_cnt_type-=1 即重试的时候 需要排除调3个奇物的位置 尝试2个奇物的位置
        edges.append(StateOperationEdge(confirm, choose_curio, status=SimUniDropCurio.STATUS_RETRY))

        super().__init__(ctx, try_times=5,
                         op_name='%s %s' % (gt('模拟宇宙', 'ui'), gt('丢弃奇物', 'ui')),
                         edges=edges
                         )

        self.config: Optional[SimUniChallengeConfig] = config
        self.skip_first_screen_check: bool = skip_first_screen_check  # 是否跳过第一次的画面状态检查 用于提速

    def _init_before_execute(self):
        super()._init_before_execute()
        self.first_screen_check = True  # 是否第一次检查画面状态
        self.curio_cnt_type: int = 3  # 奇物数量类型 3 2 1

    def _check_screen_state(self):
        screen = self.screenshot()

        if self.first_screen_check and self.skip_first_screen_check:
            self.first_screen_check = False
            return Operation.round_success(screen_state.ScreenState.SIM_DROP_CURIOS.value)

        state = screen_state.get_sim_uni_screen_state(screen, self.ctx.im, self.ctx.ocr,
                                                      drop_curio=True)

        if state is not None:
            return Operation.round_success(state)
        else:
            return Operation.round_retry('未在丢弃奇物页面', wait=1)

    def _choose_curio(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        curio_pos_list: List[MatchResult] = self._get_curio_pos(screen)
        if len(curio_pos_list) == 0:
            return Operation.round_retry('未识别到奇物', wait=1)

        target_curio_pos: Optional[MatchResult] = self._get_curio_to_choose(curio_pos_list)
        self.ctx.controller.click(target_curio_pos.center)
        time.sleep(0.25)
        self.ctx.controller.click(SimUniChooseCurio.CONFIRM_BTN.center)
        return Operation.round_success(wait=1)

    def _get_curio_pos(self, screen: MatLike) -> List[MatchResult]:
        """
        获取屏幕上的奇物的位置
        :param screen: 屏幕截图
        :return: MatchResult.data 中是对应的奇物 SimUniCurio
        """
        curio_list = self._get_curio_pos_by_rect(screen, SimUniChooseCurio.CURIO_RECT_3_LIST)
        if len(curio_list) > 0 and self.curio_cnt_type >= 3:
            return curio_list

        curio_list = self._get_curio_pos_by_rect(screen, SimUniChooseCurio.CURIO_RECT_2_LIST)
        if len(curio_list) > 0 and self.curio_cnt_type >= 2:
            return curio_list

        curio_list = self._get_curio_pos_by_rect(screen, SimUniChooseCurio.CURIO_RECT_1_LIST)
        if len(curio_list) > 0 and self.curio_cnt_type >= 1:
            return curio_list

        return []

    def _get_curio_pos_by_rect(self, screen: MatLike, rect_list: List[Rect]) -> List[MatchResult]:
        """
        获取屏幕上的奇物的位置
        :param screen: 屏幕截图
        :param rect_list: 指定区域
        :return: MatchResult.data 中是对应的奇物 SimUniCurio
        """
        curio_list: List[MatchResult] = []

        for rect in rect_list:
            title_part = cv2_utils.crop_image_only(screen, rect)
            title_ocr = self.ctx.ocr.ocr_for_single_line(title_part)
            # cv2_utils.show_image(title_part, wait=0)

            curio = match_best_curio_by_ocr(title_ocr)

            if curio is None:  # 有一个识别不到就返回 提速
                return curio_list

            log.info('识别到奇物 %s', curio)
            curio_list.append(MatchResult(1,
                                          rect.x1, rect.y1,
                                          rect.width, rect.height,
                                          data=curio))

        return curio_list

    def _get_curio_to_choose(self, curio_pos_list: List[MatchResult]) -> Optional[MatchResult]:
        """
        根据优先级选择对应的奇物
        :param curio_pos_list: 奇物列表
        :return:
        """
        curio_list = [curio.data for curio in curio_pos_list]
        target_idx = SimUniDropCurio.get_curio_by_priority(curio_list, self.config)
        if target_idx is None:
            return None
        else:
            return curio_pos_list[target_idx]

    @staticmethod
    def get_curio_by_priority(curio_list: List[SimUniCurio], config: Optional[SimUniChallengeConfig]) -> Optional[int]:
        """
        根据优先级选择对应的奇物 要丢弃的应该是优先级最低的
        :param curio_list: 可选的奇物列表
        :param config: 挑战配置
        :return: 选择的下标
        """
        if config is None:
            return 0

        opt_priority_list: List[int] = [99 for _ in curio_list]  # 选项的优先级
        cnt = 0

        for curio_enum in SimUniCurioEnum:
            curio = curio_enum.value
            if not curio.negative:  # 优先丢弃负面奇物
                continue
            for idx, opt_curio in enumerate(curio_list):
                if curio_enum.value == opt_curio and opt_priority_list[idx] == 99:
                    opt_priority_list[idx] = cnt
                    cnt += 1

        for curio_enum in SimUniCurioEnum:
            curio = curio_enum.value
            if not curio.invalid_after_got:  # 优先丢弃已失效奇物
                continue
            for idx, opt_curio in enumerate(curio_list):
                if curio_enum.value == opt_curio and opt_priority_list[idx] == 99:
                    opt_priority_list[idx] = cnt
                    cnt += 1

        for curio_id in config.curio_priority:
            curio_enum = SimUniCurioEnum[curio_id]
            for idx, opt_curio in enumerate(curio_list):
                if curio_enum.value == opt_curio and opt_priority_list[idx] == 99:
                    opt_priority_list[idx] = cnt
                    cnt += 1

        max_priority: Optional[int] = None
        max_idx: Optional[int] = None
        for idx in range(0, len(opt_priority_list)):
            if max_idx is None or opt_priority_list[idx] > max_priority:
                max_idx = idx
                max_priority = opt_priority_list[idx]

        return max_idx

    def _confirm(self) -> OperationOneRoundResult:
        """
        确认丢弃
        :return:
        """
        op = ClickDialogConfirm(self.ctx, wait_after_success=2)
        op_result = op.execute()
        if op_result.success:
            return Operation.round_success()
        else:
            self.curio_cnt_type -= 1
            if self.curio_cnt_type > 0:
                return Operation.round_success(status=SimUniDropCurio.STATUS_RETRY)
            else:
                return Operation.round_fail_by_op(op_result)

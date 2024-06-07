from typing import ClassVar, List, Optional

from cv2.typing import MatLike

from basic import Rect, Point, str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr.context import Context
from sr.image.sceenshot import screen_state
from sr.image.sceenshot.screen_state_enum import ScreenState
from sr.operation import StateOperation, OperationOneRoundResult, Operation, StateOperationNode, StateOperationEdge
from sr.screen_area.screen_sim_uni import ScreenSimUni
from sr.sim_uni.op.sim_uni_choose_bless import SimUniChooseBless, SimUniDropBless, SimUniUpgradeBless
from sr.sim_uni.op.sim_uni_choose_curio import SimUniChooseCurio, SimUniDropCurio
from sr.sim_uni.sim_uni_challenge_config import SimUniChallengeConfig


class SimUniEventOption:

    def __init__(self, title: str, title_rect: Rect, confirm_rect: Optional[Rect] = None):
        self.title: str = title
        self.title_rect: Rect = title_rect
        self.confirm_rect: Optional[Rect] = confirm_rect  # 开始对话部分的选项不需要确认


class SimUniEvent(StateOperation):

    STATUS_NO_OPT: ClassVar[str] = '无选项'
    STATUS_CHOOSE_OPT_CONFIRM: ClassVar[str] = '需确认'
    STATUS_CHOOSE_OPT_NO_CONFIRM: ClassVar[str] = '无需确认'
    STATUS_CONFIRM_SUCCESS: ClassVar[str] = '确认成功'

    OPT_RECT: ClassVar[Rect] = Rect(1335, 204, 1826, 886)  # 选项所在的地方
    EMPTY_POS: ClassVar[Point] = Point(778, 880)

    def __init__(self, ctx: Context,
                 config: Optional[SimUniChallengeConfig] = None,
                 skip_first_screen_check: bool = True):
        """
        模拟宇宙 事件
        :param ctx:
        """
        edges = []

        wait = StateOperationNode('等待加载', self._wait)
        choose_opt = StateOperationNode('选择', self._choose_opt_by_priority)
        edges.append(StateOperationEdge(wait, choose_opt))

        confirm = StateOperationNode('确认', self._confirm)
        edges.append(StateOperationEdge(choose_opt, confirm, status=SimUniEvent.STATUS_CHOOSE_OPT_CONFIRM))

        check_after_confirm = StateOperationNode('确认后判断', self._check_after_confirm)
        edges.append(StateOperationEdge(confirm, check_after_confirm, status=SimUniEvent.STATUS_CONFIRM_SUCCESS))
        edges.append(StateOperationEdge(choose_opt, check_after_confirm, status=SimUniEvent.STATUS_CHOOSE_OPT_NO_CONFIRM))

        choose_exit = StateOperationNode('选择离开', self._choose_leave)
        edges.append(StateOperationEdge(confirm, choose_exit, status='无效选项'))
        edges.append(StateOperationEdge(choose_exit, confirm))

        bless = StateOperationNode('选择祝福', self._choose_bless)
        drop_bless = StateOperationNode('丢弃祝福', self._drop_bless)
        upgrade_bless = StateOperationNode('祝福强化', op=SimUniUpgradeBless(ctx))
        curio = StateOperationNode('选择奇物', self._choose_curio)
        drop_curio = StateOperationNode('丢弃奇物', self._drop_curio)
        empty = StateOperationNode('点击空白处关闭', self._click_empty_to_continue)
        battle = StateOperationNode('战斗', self._battle)
        edges.append(StateOperationEdge(check_after_confirm, bless, status=ScreenState.SIM_BLESS.value))
        edges.append(StateOperationEdge(check_after_confirm, drop_bless, status=ScreenState.SIM_DROP_BLESS.value))
        edges.append(StateOperationEdge(check_after_confirm, upgrade_bless, status=ScreenState.SIM_UPGRADE_BLESS.value))
        edges.append(StateOperationEdge(check_after_confirm, curio, status=ScreenState.SIM_CURIOS.value))
        edges.append(StateOperationEdge(check_after_confirm, drop_curio, status=ScreenState.SIM_DROP_CURIOS.value))
        edges.append(StateOperationEdge(check_after_confirm, choose_opt, status=ScreenState.SIM_EVENT.value))
        edges.append(StateOperationEdge(check_after_confirm, empty, status=ScreenState.EMPTY_TO_CLOSE.value))
        edges.append(StateOperationEdge(check_after_confirm, battle, status=ScreenState.BATTLE.value))

        edges.append(StateOperationEdge(choose_opt, check_after_confirm, status=SimUniEvent.STATUS_NO_OPT))
        edges.append(StateOperationEdge(bless, check_after_confirm))
        edges.append(StateOperationEdge(drop_bless, check_after_confirm))
        edges.append(StateOperationEdge(upgrade_bless, check_after_confirm))
        edges.append(StateOperationEdge(curio, check_after_confirm))
        edges.append(StateOperationEdge(drop_curio, check_after_confirm))
        edges.append(StateOperationEdge(empty, check_after_confirm))
        edges.append(StateOperationEdge(battle, check_after_confirm))

        super().__init__(ctx, try_times=10,
                         op_name='%s %s' % (gt('模拟宇宙', 'ui'), gt('事件', 'ui')),
                         edges=edges,
                         # specified_start_node=bless
                         )

        self.opt_list: List[SimUniEventOption] = []
        self.config: Optional[SimUniChallengeConfig] = ctx.sim_uni_challenge_config if config is None else config
        self.skip_first_screen_check: bool = skip_first_screen_check

    def _init_before_execute(self):
        """
        执行前的初始化 注意初始化要全面 方便一个指令重复使用
        """
        super()._init_before_execute()
        self.opt_list = []
        self.chosen_opt_set: set[str] = set()  # 已经选择过的选项名称

    def _wait(self) -> OperationOneRoundResult:
        self.ctx.detect_info.view_down = False  # 进入事件后 重置视角
        if self.skip_first_screen_check:
            return self.round_success()
        screen = self.screenshot()

        if screen_state.in_sim_uni_event(screen, self.ctx.ocr):
            return self.round_success()
        else:
            return self.round_retry('未在事件页面')

    def _choose_opt_by_priority(self) -> OperationOneRoundResult:
        """
        根据优先级选一个选项
        目前固定选第一个
        :return:
        """
        screen = self.screenshot()
        self.opt_list = self._get_opt_list(screen)
        if self.ctx.one_dragon_config.is_debug:
            title = self._get_event_title(screen)
            if str_utils.find_by_lcs(gt('孤独太空美虫'), title, percent=0.5):
                return self.round_fail()

        if len(self.opt_list) == 0:
            # 有可能在对话
            self.ctx.controller.click(SimUniEvent.EMPTY_POS)
            return self.round_success(SimUniEvent.STATUS_NO_OPT, wait=0.5)
        else:
            return self._do_choose_opt(0)

    def _get_opt_list(self, screen: MatLike) -> List[SimUniEventOption]:
        """
        获取当前的选项
        :param screen:
        :return:
        """
        opt_list_1 = self._get_confirm_opt_list(screen)
        opt_list_2 = self._get_no_confirm_opt_list(screen)
        return opt_list_1 + opt_list_2

    def _get_confirm_opt_list(self, screen: MatLike) -> List[SimUniEventOption]:
        """
        获取当前需要确认的选项
        :param screen:
        :return:
        """
        part, _ = cv2_utils.crop_image(screen, SimUniEvent.OPT_RECT)
        match_result_list = self.ctx.im.match_template(part, 'event_option_icon', template_sub_dir='sim_uni',
                                                       threshold=0.7, only_best=False)

        opt_list = []
        for mr in match_result_list:
            title_lt = SimUniEvent.OPT_RECT.left_top + mr.left_top + Point(30, 0)
            title_rb = SimUniEvent.OPT_RECT.left_top + mr.right_bottom + Point(430, 0)
            title_rect = Rect(title_lt.x, title_lt.y, title_rb.x, title_rb.y)

            title_part, _ = cv2_utils.crop_image(screen, title_rect)
            title = self.ctx.ocr.ocr_for_single_line(title_part)

            confirm_lt = SimUniEvent.OPT_RECT.left_top + mr.left_top + Point(260, 85)
            confirm_rb = SimUniEvent.OPT_RECT.left_top + mr.left_top + Point(440, 165)  #
            confirm_rect = Rect(confirm_lt.x, confirm_lt.y, confirm_rb.x, confirm_rb.y)
            # confirm_part, _ = cv2_utils.crop_image(screen, confirm_rect)
            # cv2_utils.show_image(confirm_part, wait=0)

            opt = SimUniEventOption(title, title_rect, confirm_rect)
            log.info('识别需确认选项 %s', opt.title)
            opt_list.append(opt)

        return opt_list

    def _get_no_confirm_opt_list(self, screen: MatLike) -> List[SimUniEventOption]:
        """
        获取当前不需要确认的选项
        :param screen:
        :return:
        """
        part, _ = cv2_utils.crop_image(screen, SimUniEvent.OPT_RECT)
        opt_list = []
        template_id_list = [
            'event_option_no_confirm_icon',
            'event_option_enhance_icon',
            'event_option_exit_icon'
        ]

        for template_id in template_id_list:
            match_result_list = self.ctx.im.match_template(part, template_id, template_sub_dir='sim_uni',
                                                           threshold=0.7, only_best=False)

            for mr in match_result_list:
                title_lt = SimUniEvent.OPT_RECT.left_top + mr.left_top + Point(50, 0)
                title_rb = SimUniEvent.OPT_RECT.left_top + mr.right_bottom + Point(430, 0)
                title_rect = Rect(title_lt.x, title_lt.y, title_rb.x, title_rb.y)

                title_part, _ = cv2_utils.crop_image(screen, title_rect)
                title = self.ctx.ocr.ocr_for_single_line(title_part)

                opt = SimUniEventOption(title, title_rect)
                log.info('识别无需选项 %s', opt.title)
                opt_list.append(opt)

        return opt_list

    def _confirm(self):
        click = self.ocr_and_click_one_line('确认', self.chosen_opt.confirm_rect)
        if click == Operation.OCR_CLICK_SUCCESS:
            return self.round_success(SimUniEvent.STATUS_CONFIRM_SUCCESS, wait=2)
        elif click == Operation.OCR_CLICK_NOT_FOUND:
            return self.round_success('无效选项')
        else:
            return self.round_success('点击确认失败', wait=0.25)

    def _do_choose_opt(self, idx: int) -> OperationOneRoundResult:
        """
        选择一个事件选项
        :param idx:
        :return:
        """
        click = self.ctx.controller.click(self.opt_list[idx].title_rect.center)
        if click:
            self.chosen_opt = self.opt_list[idx]
            self.chosen_opt_set.add(self.chosen_opt.title)
            if self.chosen_opt.confirm_rect is None:
                status = SimUniEvent.STATUS_CHOOSE_OPT_NO_CONFIRM
                return self.round_success(status, wait=1.5)
            else:
                status = SimUniEvent.STATUS_CHOOSE_OPT_CONFIRM
                return self.round_success(status, wait=1)
        else:
            return self.round_retry('点击选项失败', wait=0.5)

    def _choose_leave(self):
        """
        选择最后一个代表离开
        :return:
        """
        idx = len(self.opt_list) - 1

        # 部分事件没有离开选项 且最后一个选项可能无法选择 这里需要遍历还没有选过的选项
        while True:
            title = self.opt_list[idx].title
            chosen: bool = False
            for chosen_title in self.chosen_opt_set:
                if str_utils.find_by_lcs(chosen_title, title, percent=0.8):
                    chosen = True
                    break
            if chosen:
                idx -= 1
                if idx < 0:  # 应该不存在这种情况
                    return self.round_fail('所有选项都无效')
            else:
                break

        return self._do_choose_opt(idx)

    def _check_after_confirm(self) -> OperationOneRoundResult:
        """
        确认后判断下一步动作
        :return:
        """
        screen = self.screenshot()
        state = self._get_screen_state(screen)
        if state is None:
            return self.round_retry('未能判断当前页面', wait=1)
        else:
            return self.round_success(state)

    def _get_screen_state(self, screen: MatLike) -> Optional[str]:
        state = screen_state.get_sim_uni_screen_state(screen, self.ctx.im, self.ctx.ocr,
                                                      in_world=True,
                                                      empty_to_close=True,
                                                      bless=True,
                                                      drop_bless=True,
                                                      upgrade_bless=True,
                                                      curio=True,
                                                      drop_curio=True,
                                                      event=True,
                                                      battle=True)
        log.info('当前画面状态 %s', state)
        if state is not None:
            return state

        # 未知情况都先点击一下
        self.ctx.controller.click(screen_state.TargetRect.EMPTY_TO_CLOSE.value.center)
        return None

    def _choose_bless(self) -> OperationOneRoundResult:
        op = SimUniChooseBless(self.ctx, config=self.config)
        op_result = op.execute()

        if op_result.success:
            return self.round_success(wait=1)
        else:
            return self.round_retry(status=op_result.status)

    def _drop_bless(self) -> OperationOneRoundResult:
        op = SimUniDropBless(self.ctx, config=self.config)
        op_result = op.execute()

        if op_result.success:
            return self.round_success()
        else:
            return self.round_retry(status=op_result.status)

    def _choose_curio(self) -> OperationOneRoundResult:
        op = SimUniChooseCurio(self.ctx, config=self.config)
        op_result = op.execute()

        if op_result.success:
            return self.round_success()
        else:
            return self.round_retry(status=op_result.status)

    def _drop_curio(self) -> OperationOneRoundResult:
        op = SimUniDropCurio(self.ctx, config=self.config)
        op_result = op.execute()

        if op_result.success:
            return self.round_success()
        else:
            return self.round_retry(status=op_result.status)

    def _click_empty_to_continue(self) -> OperationOneRoundResult:
        click = self.ctx.controller.click(screen_state.TargetRect.EMPTY_TO_CLOSE.value.center)

        if click:
            return self.round_success(wait=2)  # 通过是丢弃或者得到奇物祝福 有可能有二段确认 因此多等待久一点时间
        else:
            return self.round_retry('点击空白处关闭失败')

    def _battle(self) -> OperationOneRoundResult:
        # op = SimUniEnterFight(self.ctx,
        #                       bless_config=self.bless_priority,
        #                       curio_config=self.curio_priority)
        # op_result = op.execute()
        #
        # if op_result.success:
        #     return self.round_success()
        # else:
        #     return self.round_fail(status=op_result.status)
        # 这里似乎不用进去战斗画面也可以
        return self.round_success(wait=1)

    def _get_event_title(self, screen: MatLike) -> str:
        """
        获取当前事件的名称
        :return:
        """
        area = ScreenSimUni.EVENT_TITLE.value
        part = cv2_utils.crop_image_only(screen, area.rect)
        return self.ctx.ocr.ocr_for_single_line(part)

from typing import Optional, List, ClassVar, Callable

from basic import Rect
from basic.i18_utils import gt
from basic.log_utils import log
from sr.app.app_description import AppDescriptionEnum
from sr.app.app_run_record import AppRunRecord
from sr.app.application_base import Application2
from sr.app.sim_uni.sim_uni_config import SimUniConfig
from sr.app.sim_uni.sim_uni_run_record import SimUniRunRecord, get_record
from sr.app.sim_uni.sim_uni_run_world import SimUniRunWorld
from sr.const import phone_menu_const
from sr.context import Context
from sr.image.sceenshot import screen_state
from sr.interastral_peace_guide.survival_index_mission import SurvivalIndexCategoryEnum
from sr.operation import OperationResult, Operation, StateOperationEdge, StateOperationNode, \
    OperationOneRoundResult
from sr.operation.unit.back_to_world import BackToWorld
from sr.operation.unit.guide import GuideTabEnum
from sr.operation.unit.guide.choose_guide_tab import ChooseGuideTab
from sr.operation.unit.guide.mission_transport import ChooseGuideMissionCategory
from sr.operation.unit.menu.click_phone_menu_item import ClickPhoneMenuItem
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu
from sr.screen_area.sim_uni import ScreenSimUniEntry
from sr.sim_uni.op.choose_sim_uni_diff import ChooseSimUniDiff
from sr.sim_uni.op.choose_sim_uni_num import ChooseSimUniNum
from sr.sim_uni.op.choose_sim_uni_path import ChooseSimUniPath
from sr.sim_uni.op.choose_sim_uni_type import ChooseSimUniType
from sr.sim_uni.op.sim_uni_battle import SimUniEnterFight
from sr.sim_uni.op.sim_uni_claim_weekly_reward import SimUniClaimWeeklyReward
from sr.sim_uni.op.sim_uni_exit import SimUniExit
from sr.sim_uni.op.sim_uni_start import SimUniStart
from sr.sim_uni.sim_uni_const import SimUniType, SimUniPath, SimUniWorldEnum


class SimUniApp(Application2):

    STATUS_ALL_FINISHED: ClassVar[str] = '已完成通关次数'
    STATUS_EXCEPTION: ClassVar[str] = '异常次数过多'

    def __init__(self, ctx: Context,
                 specified_uni_num: Optional[int] = None,
                 max_reward_to_get: int = 0,
                 get_reward_callback: Optional[Callable[[int, int], None]] = None):
        """
        模拟宇宙应用 需要在大世界中非战斗、非特殊关卡界面中开启
        :param ctx:
        """
        gc = ctx.game_config
        self.config: SimUniConfig = ctx.sim_uni_config

        edges: List[StateOperationEdge] = []

        check_times = StateOperationNode('检查运行次数', self._check_times)
        check_initial_screen = StateOperationNode('检查初始画面', self._check_initial_screen)
        edges.append(StateOperationEdge(check_times, check_initial_screen))

        check_reward_before_exit = StateOperationNode('领取每周奖励', op=SimUniClaimWeeklyReward(ctx))
        edges.append(StateOperationEdge(check_times, check_reward_before_exit, status=SimUniApp.STATUS_ALL_FINISHED))

        back_to_world = StateOperationNode('退出', op=BackToWorld(ctx))  # 无论是否领取成功都退出
        edges.append(StateOperationEdge(check_reward_before_exit, back_to_world, ignore_status=True))
        edges.append(StateOperationEdge(check_reward_before_exit, back_to_world, success=False, ignore_status=True))

        open_menu = StateOperationNode('菜单', op=OpenPhoneMenu(ctx))
        edges.append(StateOperationEdge(check_initial_screen, open_menu, ignore_status=True))

        choose_guide = StateOperationNode('指南', op=ClickPhoneMenuItem(ctx, phone_menu_const.INTERASTRAL_GUIDE))
        edges.append(StateOperationEdge(open_menu, choose_guide))
        edges.append(StateOperationEdge(check_initial_screen, choose_guide,
                                        status=screen_state.ScreenState.PHONE_MENU.value))  # 在菜单的时候 打开指南

        choose_survival_index = StateOperationNode('生存索引', op=ChooseGuideTab(ctx, GuideTabEnum.TAB_3.value))
        edges.append(StateOperationEdge(choose_guide, choose_survival_index))
        edges.append(StateOperationEdge(check_initial_screen, choose_survival_index,
                                        status=screen_state.ScreenState.GUIDE.value))  # 在指南里 选择生存索引

        choose_sim_category = StateOperationNode('模拟宇宙', op=ChooseGuideMissionCategory(ctx, SurvivalIndexCategoryEnum.SIM_UNI.value))
        edges.append(StateOperationEdge(choose_survival_index, choose_sim_category))
        edges.append(StateOperationEdge(check_initial_screen, choose_sim_category,
                                        status=screen_state.ScreenState.GUIDE_SURVIVAL_INDEX.value))  # 在生存索引 选择模拟宇宙

        transport = StateOperationNode('传送', self._transport)
        edges.append(StateOperationEdge(choose_sim_category, transport))

        choose_normal_universe = StateOperationNode('普通宇宙', op=ChooseSimUniType(ctx, SimUniType.NORMAL))
        edges.append(StateOperationEdge(transport, choose_normal_universe))
        edges.append(StateOperationEdge(check_initial_screen, choose_normal_universe,
                                        status=screen_state.ScreenState.SIM_TYPE_EXTEND.value))  # 拓展装置 选择模拟宇宙

        choose_universe_num = StateOperationNode('选择世界', self._choose_sim_uni_num)
        edges.append(StateOperationEdge(choose_normal_universe, choose_universe_num))
        edges.append(StateOperationEdge(check_initial_screen, choose_universe_num,
                                        status=screen_state.ScreenState.SIM_TYPE_NORMAL.value))  # 模拟宇宙 选择世界

        choose_universe_diff = StateOperationNode('选择难度', self._choose_sim_uni_diff)
        edges.append(StateOperationEdge(choose_universe_num, choose_universe_diff,
                                        status=ChooseSimUniNum.STATUS_RESTART))

        start_sim = StateOperationNode('开始挑战', op=SimUniStart(ctx))
        edges.append(StateOperationEdge(choose_universe_diff, start_sim))
        edges.append(StateOperationEdge(choose_universe_num, start_sim,
                                        status=ChooseSimUniNum.STATUS_CONTINUE))

        choose_path = StateOperationNode('选择命途', self._choose_path)
        edges.append(StateOperationEdge(start_sim, choose_path, status=SimUniStart.STATUS_RESTART))

        run_world = StateOperationNode('通关', self._run_world)
        edges.append(StateOperationEdge(choose_path, run_world))
        edges.append(StateOperationEdge(start_sim, run_world, status=ChooseSimUniNum.STATUS_CONTINUE))

        # 战斗成功
        check_times_to_continue = StateOperationNode('继续检查运行次数', self._check_times)
        edges.append(StateOperationEdge(run_world, check_times_to_continue))
        edges.append(StateOperationEdge(check_times_to_continue, choose_universe_num))
        edges.append(StateOperationEdge(check_times_to_continue, check_reward_before_exit, status=SimUniApp.STATUS_ALL_FINISHED))
        edges.append(StateOperationEdge(check_times_to_continue, check_reward_before_exit, status=SimUniApp.STATUS_EXCEPTION))

        # 战斗失败
        world_fail = StateOperationNode('战斗失败', op=SimUniExit(ctx, exit_clicked=True))
        edges.append(StateOperationEdge(run_world, world_fail,
                                        success=False, status=SimUniEnterFight.STATUS_BATTLE_FAIL))
        edges.append(StateOperationEdge(world_fail, check_times_to_continue))

        if not gc.is_debug:  # 任何异常错误都退出当前宇宙 调试模式下不退出 直接失败等待处理
            exception_exit = StateOperationNode('异常退出', self._exception_exit)
            edges.append(StateOperationEdge(run_world, exception_exit,
                                            success=False, ignore_status=True))
            edges.append(StateOperationEdge(exception_exit, check_times_to_continue))

        self.run_record: SimUniRunRecord = get_record()
        super().__init__(ctx, op_name=gt(AppDescriptionEnum.SIM_UNIVERSE.value.cn, 'ui'),
                         edges=edges, specified_start_node=check_times,
                         run_record=self.run_record)

        self.current_uni_num: int = 0  # 当前运行的第几宇宙 启动时会先完成运行中的宇宙

        self.specified_uni_num: Optional[int] = specified_uni_num  # 指定宇宙 用于沉浸奖励
        self.max_reward_to_get: int = max_reward_to_get  # 最多获取多少次奖励
        self.get_reward_cnt: int = 0  # 当前获取的奖励次数
        self.get_reward_callback: Optional[Callable[[int, int], None]] = get_reward_callback  # 获取奖励后的回调

        self.exception_times: int = 0  # 异常出现次数

    def _init_before_execute(self):
        super()._init_before_execute()
        self.get_reward_cnt = 0
        self.exception_times: int = 0

    def _check_times(self) -> OperationOneRoundResult:
        if self.specified_uni_num is not None:
            if self.get_reward_cnt < self.max_reward_to_get:
                return Operation.round_success()
            else:
                return Operation.round_success(SimUniApp.STATUS_ALL_FINISHED)

        if self.exception_times >= 10:
            return Operation.round_success(SimUniApp.STATUS_EXCEPTION)

        log.info('本日通关次数 %d 本周通关次数 %d', self.run_record.daily_times, self.run_record.weekly_times)
        if self.run_record.run_status_under_now == AppRunRecord.STATUS_SUCCESS:
            return Operation.round_success(SimUniApp.STATUS_ALL_FINISHED)
        else:
            return Operation.round_success()

    def _check_initial_screen(self) -> OperationOneRoundResult:
        screen = self.screenshot()
        return Operation.round_success(screen_state.get_sim_uni_initial_screen_state(screen, self.ctx.im, self.ctx.ocr))

    def _transport(self) -> OperationOneRoundResult:
        """
        点击传送
        :return:
        """
        click = self.find_and_click_area(ScreenSimUniEntry.GUIDE_TRANSPORT.value)
        if click == Operation.OCR_CLICK_SUCCESS:
            return Operation.round_success(wait=3)
        else:
            return Operation.round_retry('点击传送失败', wait=1)

    def _choose_sim_uni_num(self) -> OperationOneRoundResult:
        if self.specified_uni_num is None:
            world = SimUniWorldEnum[self.config.weekly_uni_num]
        else:
            world = SimUniWorldEnum['WORLD_%02d' % self.specified_uni_num]
        op = ChooseSimUniNum(self.ctx, world.value.idx, op_callback=self._on_uni_num_chosen)
        return Operation.round_by_op(op.execute())

    def _choose_sim_uni_diff(self) -> OperationOneRoundResult:
        op = ChooseSimUniDiff(self.ctx, self.config.weekly_uni_diff)
        return Operation.round_by_op(op.execute())

    def _on_uni_num_chosen(self, op_result: OperationResult):
        if op_result.success:
            self.current_uni_num = op_result.data

    def _choose_path(self) -> OperationOneRoundResult:
        """
        选择命途
        :return:
        """
        cfg = self.config.get_challenge_config(self.current_uni_num)
        op = ChooseSimUniPath(self.ctx, SimUniPath[cfg.path])
        return Operation.round_by_op(op.execute())

    def _run_world(self) -> OperationOneRoundResult:
        uni_challenge_config = self.config.get_challenge_config(self.current_uni_num)
        get_reward = self.current_uni_num == self.specified_uni_num  # 只有当前宇宙和开拓力需要的宇宙是同一个 才能拿奖励

        op = SimUniRunWorld(self.ctx, self.current_uni_num,
                            config=uni_challenge_config,
                            op_callback=self.on_world_finished,
                            max_reward_to_get=self.max_reward_to_get - self.get_reward_cnt if get_reward else 0,
                            get_reward_callback=self._on_sim_uni_get_reward if get_reward else None
                            )
        return Operation.round_by_op(op.execute())

    def _on_sim_uni_get_reward(self, use_power: int, user_qty: int):
        self.get_reward_cnt += 1
        if self.get_reward_callback is not None:
            self.get_reward_callback(use_power, user_qty)

    def on_world_finished(self, op_result: OperationResult):
        if op_result.success:
            self.run_record.add_times()

    def _exception_exit(self) -> OperationOneRoundResult:
        self.exception_times += 1
        op = SimUniExit(self.ctx, exit_clicked=False)
        return Operation.round_by_op(op.execute())

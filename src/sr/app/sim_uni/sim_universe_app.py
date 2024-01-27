from typing import Optional, List, ClassVar

from basic import os_utils
from basic.i18_utils import gt
from basic.log_utils import log
from sr.app import AppDescription, register_app, AppRunRecord, Application2, app_record_current_dt_str
from sr.app.sim_uni.sim_uni_config import SimUniAppConfig, get_sim_uni_app_config
from sr.app.sim_uni.sim_uni_run_world import SimUniRunWorld
from sr.const import phone_menu_const
from sr.context import Context
from sr.operation import OperationResult, Operation, StateOperationEdge, StateOperationNode, \
    OperationOneRoundResult
from sr.operation.unit.back_to_world import BackToWorld
from sr.operation.unit.guide import GUIDE_TAB_3
from sr.operation.unit.guide.choose_guide_tab import ChooseGuideTab
from sr.operation.unit.guide.mission_transport import ChooseGuideMissionCategory, CATEGORY_ROGUE, ChooseGuideMission, \
    MISSION_SIM_UNIVERSE
from sr.operation.unit.menu.click_phone_menu_item import ClickPhoneMenuItem
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu
from sr.sim_uni.op.choose_sim_uni_diff import ChooseSimUniDiff
from sr.sim_uni.op.choose_sim_uni_num import ChooseSimUniNum
from sr.sim_uni.op.choose_sim_uni_path import ChooseSimUniPath
from sr.sim_uni.op.choose_sim_uni_type import ChooseSimUniType
from sr.sim_uni.op.sim_uni_battle import SimUniEnterFight
from sr.sim_uni.op.sim_uni_exit import SimUniExit
from sr.sim_uni.op.sim_uni_start import SimUniStart
from sr.sim_uni.sim_uni_const import SimUniType, SimUniPath, SimUniWorldEnum

SIM_UNIVERSE = AppDescription(cn='模拟宇宙', id='sim_universe')
register_app(SIM_UNIVERSE)


class SimUniverseRecord(AppRunRecord):

    def __init__(self):
        super().__init__(SIM_UNIVERSE.id)
        self.config = get_sim_uni_app_config()

    @property
    def run_status_under_now(self):
        """
        基于当前时间显示的运行状态
        :return:
        """
        if self._should_reset_by_dt():
            if os_utils.is_monday(app_record_current_dt_str()):
                return AppRunRecord.STATUS_WAIT
            elif self.weekly_times >= self.config.weekly_times:  # 已完成本周次数
                return AppRunRecord.STATUS_SUCCESS
            else:
                return AppRunRecord.STATUS_WAIT
        else:
            if self.daily_times >= self.config.daily_times:  # 已完成本日次数
                return AppRunRecord.STATUS_SUCCESS
            else:
                return AppRunRecord.STATUS_WAIT

    def reset_record(self):
        """
        运行记录重置 非公共部分由各app自行实现
        :return:
        """
        super().reset_record()
        current_dt = app_record_current_dt_str()
        if os_utils.get_money_dt(current_dt) != os_utils.get_money_dt(self.dt):
            self.weekly_times = 0
        self.daily_times = 0

    def add_times(self):
        """
        增加一次完成次数
        :return:
        """
        self.daily_times = self.daily_times + 1
        self.weekly_times = self.weekly_times + 1

    @property
    def weekly_times(self) -> int:
        """
        每周挑战的次数
        :return:
        """
        return self.get('weekly_times', 0)

    @weekly_times.setter
    def weekly_times(self, new_value: int):
        self.update('weekly_times', new_value)

    @property
    def daily_times(self) -> int:
        """
        每天挑战的次数
        :return:
        """
        return self.get('daily_times', 0)

    @daily_times.setter
    def daily_times(self, new_value: int):
        self.update('daily_times', new_value)


sim_universe_record: Optional[SimUniverseRecord] = None


def get_record() -> SimUniverseRecord:
    global sim_universe_record
    if sim_universe_record is None:
        sim_universe_record = SimUniverseRecord()
    return sim_universe_record


class SimUniverseApp(Application2):

    STATUS_ALL_FINISHED: ClassVar[str] = '已完成通关次数'

    def __init__(self, ctx: Context):
        """
        模拟宇宙应用 需要在大世界中非战斗、非特殊关卡界面中开启
        :param ctx:
        """
        self.config: SimUniAppConfig = get_sim_uni_app_config()

        edges: List[StateOperationEdge] = []

        check_times = StateOperationNode('检查运行次数', self._check_times)

        back_to_world = StateOperationNode('退出', op=BackToWorld(ctx))
        edges.append(StateOperationEdge(check_times, back_to_world, status=SimUniverseApp.STATUS_ALL_FINISHED))

        open_menu = StateOperationNode('菜单', op=OpenPhoneMenu(ctx))
        edges.append(StateOperationEdge(check_times, open_menu))

        choose_guide = StateOperationNode('指南', op=ClickPhoneMenuItem(ctx, phone_menu_const.INTERASTRAL_GUIDE))
        edges.append(StateOperationEdge(open_menu, choose_guide))

        choose_survival_index = StateOperationNode('生存索引', op=ChooseGuideTab(ctx, GUIDE_TAB_3))
        edges.append(StateOperationEdge(choose_guide, choose_survival_index))

        choose_sim_category = StateOperationNode('模拟宇宙', op=ChooseGuideMissionCategory(ctx, CATEGORY_ROGUE))
        edges.append(StateOperationEdge(choose_survival_index, choose_sim_category))

        transport = StateOperationNode('传送', op=ChooseGuideMission(ctx, MISSION_SIM_UNIVERSE))
        edges.append(StateOperationEdge(choose_sim_category, transport))

        choose_normal_universe = StateOperationNode('普通宇宙', op=ChooseSimUniType(ctx, SimUniType.NORMAL))
        edges.append(StateOperationEdge(transport, choose_normal_universe))

        choose_universe_num = StateOperationNode('选择世界', self._choose_sim_uni_num)
        edges.append(StateOperationEdge(choose_normal_universe, choose_universe_num))

        choose_universe_diff = StateOperationNode('选择难度', self._choose_sim_uni_diff)
        edges.append(StateOperationEdge(choose_universe_num, choose_universe_diff,
                                        status=ChooseSimUniNum.STATUS_RESTART))

        start_sim = StateOperationNode('开始挑战', op=SimUniStart(ctx))
        edges.append(StateOperationEdge(choose_universe_diff, start_sim))
        edges.append(StateOperationEdge(choose_universe_num, start_sim,
                                        status=ChooseSimUniNum.STATUS_CONTINUE))

        choose_path = StateOperationNode('选择命途', op=ChooseSimUniPath(ctx, SimUniPath.PROPAGATION))
        edges.append(StateOperationEdge(start_sim, choose_path, status=SimUniStart.STATUS_RESTART))

        run_world = StateOperationNode('通关', self._run_world)
        edges.append(StateOperationEdge(choose_path, run_world))
        edges.append(StateOperationEdge(start_sim, run_world, status=ChooseSimUniNum.STATUS_CONTINUE))

        # 战斗成功
        check_times_to_continue = StateOperationNode('继续检查运行次数', self._check_times)
        edges.append(StateOperationEdge(run_world, check_times_to_continue))
        edges.append(StateOperationEdge(check_times_to_continue, choose_universe_num))

        # 战斗失败
        world_fail = StateOperationNode('战斗失败', op=SimUniExit(ctx, exit_clicked=True))
        edges.append(StateOperationEdge(run_world, world_fail,
                                        success=False, status=SimUniEnterFight.STATUS_BATTLE_FAIL))
        edges.append(StateOperationEdge(world_fail, check_times_to_continue))

        # 执行超时 - 应该只有寻路卡住的情况
        timeout = StateOperationNode('执行超时', op=SimUniExit(ctx, exit_clicked=False))
        edges.append(StateOperationEdge(run_world, timeout,
                                        success=False, status=Operation.STATUS_TIMEOUT))
        edges.append(StateOperationEdge(timeout, check_times_to_continue))

        self.run_record: SimUniverseRecord = get_record()
        super().__init__(ctx, op_name=gt(SIM_UNIVERSE.cn, 'ui'),
                         edges=edges, specified_start_node=check_times,
                         run_record=self.run_record)

        self.current_uni_num: int = 8

    def _init_before_execute(self):
        super()._init_before_execute()

    def _check_times(self) -> OperationOneRoundResult:
        log.info('本日通关次数 %d 本周通关次数 %d', self.run_record.daily_times, self.run_record.weekly_times)
        if self.run_record.run_status_under_now == AppRunRecord.STATUS_SUCCESS:
            return Operation.round_success(SimUniverseApp.STATUS_ALL_FINISHED)
        else:
            return Operation.round_success()

    def _choose_sim_uni_num(self) -> OperationOneRoundResult:
        world = SimUniWorldEnum[self.config.weekly_uni_num]
        op = ChooseSimUniNum(self.ctx, world.value.idx, op_callback=self._on_uni_num_chosen)
        return Operation.round_by_op(op.execute())

    def _choose_sim_uni_diff(self) -> OperationOneRoundResult:
        op = ChooseSimUniDiff(self.ctx, self.config.weekly_uni_diff)
        return Operation.round_by_op(op.execute())

    def _on_uni_num_chosen(self, op_result: OperationResult):
        if op_result.success:
            self.current_uni_num = op_result.data

    def _run_world(self) -> OperationOneRoundResult:
        uni_challenge_config = self.config.get_challenge_config(self.current_uni_num)
        op = SimUniRunWorld(self.ctx, self.current_uni_num,
                            priority=uni_challenge_config.all_priority,
                            op_callback=self.on_world_finished
                            )
        return Operation.round_by_op(op.execute())

    def on_world_finished(self, op_result: OperationResult):
        if op_result.success:
            self.run_record.add_times()

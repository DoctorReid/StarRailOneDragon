from typing import Optional, List, ClassVar

from basic import os_utils
from basic.i18_utils import gt
from sr.app import AppDescription, register_app, AppRunRecord, Application2, app_record_current_dt_str
from sr.app.sim_uni.sim_uni_config import SimUniAppConfig, get_sim_uni_app_config
from sr.app.sim_uni.sim_uni_run_world import SimUniRunWorld
from sr.const import phone_menu_const
from sr.context import Context
from sr.operation import OperationResult, Operation, OperationSuccess
from sr.operation.combine import StatusCombineOperationEdge2, StatusCombineOperationNode
from sr.operation.unit.guide import GUIDE_TAB_3
from sr.operation.unit.guide.choose_guide_tab import ChooseGuideTab
from sr.operation.unit.guide.mission_transport import ChooseGuideMissionCategory, CATEGORY_ROGUE, ChooseGuideMission, \
    MISSION_SIM_UNIVERSE
from sr.operation.unit.menu.click_phone_menu_item import ClickPhoneMenuItem
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu
from sr.sim_uni.op.sim_uni_battle import SimUniEnterFight
from sr.sim_uni.op.choose_sim_uni_diff import ChooseSimUniDiff
from sr.sim_uni.op.choose_sim_uni_num import ChooseSimUniNum
from sr.sim_uni.op.choose_sim_uni_path import ChooseSimUniPath
from sr.sim_uni.op.choose_sim_uni_type import ChooseSimUniType
from sr.sim_uni.op.sim_uni_exit import SimUniExit
from sr.sim_uni.op.sim_uni_start import SimUniStart
from sr.sim_uni.sim_uni_const import SimUniType, SimUniPath, SimUniWorldEnum
from sr.sim_uni.sim_uni_priority import SimUniBlessPriority, SimUniNextLevelPriority, SimUniCurioPriority

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
        if os_utils.is_monday(app_record_current_dt_str()):
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

    STATUS_ALL_FINISHED: ClassVar[str] = '已完成设定次数'

    def __init__(self, ctx: Context):
        """
        模拟宇宙应用 需要在大世界中非战斗、非特殊关卡界面中开启
        :param ctx:
        """
        self.config: SimUniAppConfig = get_sim_uni_app_config()

        edges: List[StatusCombineOperationEdge2] = []

        open_menu = StatusCombineOperationNode('菜单', OpenPhoneMenu(ctx))
        choose_guide = StatusCombineOperationNode('指南', ClickPhoneMenuItem(ctx, phone_menu_const.INTERASTRAL_GUIDE))
        edges.append(StatusCombineOperationEdge2(open_menu, choose_guide))

        choose_survival_index = StatusCombineOperationNode('生存索引', ChooseGuideTab(ctx, GUIDE_TAB_3))
        edges.append(StatusCombineOperationEdge2(choose_guide, choose_survival_index))

        choose_sim_category = StatusCombineOperationNode('模拟宇宙', ChooseGuideMissionCategory(ctx, CATEGORY_ROGUE))
        edges.append(StatusCombineOperationEdge2(choose_survival_index, choose_sim_category))

        transport = StatusCombineOperationNode('传送', ChooseGuideMission(ctx, MISSION_SIM_UNIVERSE))
        edges.append(StatusCombineOperationEdge2(choose_sim_category, transport))

        choose_normal_universe = StatusCombineOperationNode('普通宇宙', ChooseSimUniType(ctx, SimUniType.NORMAL))
        edges.append(StatusCombineOperationEdge2(transport, choose_normal_universe))

        choose_universe_num = StatusCombineOperationNode('选择世界', op_func=self._choose_sim_uni_num)
        edges.append(StatusCombineOperationEdge2(choose_normal_universe, choose_universe_num))

        choose_universe_diff = StatusCombineOperationNode('选择难度', op_func=self._choose_sim_uni_diff)
        edges.append(StatusCombineOperationEdge2(choose_universe_num, choose_universe_diff, status=ChooseSimUniNum.STATUS_RESTART))

        start_sim = StatusCombineOperationNode('开始挑战', SimUniStart(ctx))
        edges.append(StatusCombineOperationEdge2(choose_universe_diff, start_sim))
        edges.append(StatusCombineOperationEdge2(choose_universe_num, start_sim, status=ChooseSimUniNum.STATUS_CONTINUE))

        choose_path = StatusCombineOperationNode('选择命途', ChooseSimUniPath(ctx, SimUniPath.PROPAGATION))
        edges.append(StatusCombineOperationEdge2(start_sim, choose_path, status=SimUniStart.STATUS_RESTART))

        run_world = StatusCombineOperationNode('通关', op_func=self._run_world)
        edges.append(StatusCombineOperationEdge2(choose_path, run_world))
        edges.append(StatusCombineOperationEdge2(start_sim, run_world, status=ChooseSimUniNum.STATUS_CONTINUE))

        # 战斗成功
        finished = StatusCombineOperationNode('完成次数', OperationSuccess(ctx))
        edges.append(StatusCombineOperationEdge2(run_world, finished, status=SimUniverseApp.STATUS_ALL_FINISHED))
        edges.append(StatusCombineOperationEdge2(run_world, choose_universe_num, ignore_status=True))

        # 战斗失败
        world_fail = StatusCombineOperationNode('战斗失败', SimUniExit(ctx, exit_clicked=True))
        edges.append(StatusCombineOperationEdge2(run_world, world_fail, success=False, status=SimUniEnterFight.STATUS_BATTLE_FAIL))
        edges.append(StatusCombineOperationEdge2(world_fail, choose_universe_num))

        self.run_record: SimUniverseRecord = get_record()
        super().__init__(ctx, op_name=gt(SIM_UNIVERSE.cn, 'ui'),
                         edges=edges,
                         run_record=self.run_record)

        self.current_uni_num: int = 8

    def _init_before_execute(self):
        super()._init_before_execute()

    def _choose_sim_uni_num(self) -> Operation:
        world = SimUniWorldEnum[self.config.weekly_uni_num]
        return ChooseSimUniNum(self.ctx, world.value.idx, op_callback=self._on_uni_num_chosen)

    def _choose_sim_uni_diff(self) -> Operation:
        return ChooseSimUniDiff(self.ctx, self.config.weekly_uni_diff)

    def _on_uni_num_chosen(self, op_result: OperationResult):
        if op_result.success:
            self.current_uni_num = op_result.data

    def _run_world(self) -> Operation:
        if self.run_record.run_status_under_now == AppRunRecord.STATUS_SUCCESS:
            return OperationSuccess(self.ctx, status=SimUniverseApp.STATUS_ALL_FINISHED)
        uni_challenge_config = self.config.get_challenge_config(self.current_uni_num)
        return SimUniRunWorld(self.ctx, self.current_uni_num,
                              bless_priority=SimUniBlessPriority(uni_challenge_config.bless_priority, uni_challenge_config.bless_priority_2),
                              curio_priority=SimUniCurioPriority(uni_challenge_config.curio_priority),
                              next_level_priority=SimUniNextLevelPriority(uni_challenge_config.level_type_priority),
                              op_callback=self.on_world_finished
                              )

    def on_world_finished(self, op_result: OperationResult):
        if op_result.success:
            self.run_record.add_times()

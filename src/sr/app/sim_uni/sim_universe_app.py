from typing import Optional, List

from basic.i18_utils import gt
from sr.app import AppDescription, register_app, AppRunRecord, Application2
from sr.app.sim_uni.sim_uni_run_world import SimUniRunWorld
from sr.const import phone_menu_const
from sr.context import Context
from sr.operation import OperationResult
from sr.operation.combine import StatusCombineOperationEdge2, StatusCombineOperationNode
from sr.operation.unit.guide import GUIDE_TAB_3
from sr.operation.unit.guide.choose_guide_tab import ChooseGuideTab
from sr.operation.unit.guide.mission_transport import ChooseGuideMissionCategory, CATEGORY_ROGUE, ChooseGuideMission, \
    MISSION_SIM_UNIVERSE
from sr.operation.unit.menu.click_phone_menu_item import ClickPhoneMenuItem
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu
from sr.sim_uni.sim_uni_const import SimUniType, SimUniPath, SimUniLevelTypeEnum
from sr.sim_uni.op.choose_sim_uni_diff import ChooseSimUniDiff
from sr.sim_uni.op.choose_sim_uni_num import ChooseSimUniNum
from sr.sim_uni.op.choose_sim_uni_path import ChooseSimUniPath
from sr.sim_uni.op.choose_sim_uni_type import ChooseSimUniType
from sr.sim_uni.op.sim_uni_start import SimUniStart
from sr.sim_uni.sim_uni_priority import SimUniBlessPriority, SimUniNextLevelPriority

SIM_UNIVERSE = AppDescription(cn='模拟宇宙', id='sim_universe')
register_app(SIM_UNIVERSE)


class SimUniverseRecord(AppRunRecord):

    def __init__(self):
        super().__init__(SIM_UNIVERSE.id)


sim_universe_record: Optional[SimUniverseRecord] = None


def get_record() -> SimUniverseRecord:
    global sim_universe_record
    if sim_universe_record is None:
        sim_universe_record = SimUniverseRecord()
    return sim_universe_record


class SimUniverseApp(Application2):

    def __init__(self, ctx: Context):
        """
        模拟宇宙应用 需要在大世界中非战斗、非特殊关卡界面中开启
        :param ctx:
        """
        bless_priority = SimUniBlessPriority(SimUniPath.PROPAGATION.value)
        next_level_priority = SimUniNextLevelPriority(SimUniLevelTypeEnum.COMBAT.value.type_id)

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

        choose_universe_num = StatusCombineOperationNode('选择世界', ChooseSimUniNum(ctx, 8, op_callback=self._on_uni_num_chosen))
        edges.append(StatusCombineOperationEdge2(choose_normal_universe, choose_universe_num))

        choose_universe_diff = StatusCombineOperationNode('选择难度', ChooseSimUniDiff(ctx, 4))
        edges.append(StatusCombineOperationEdge2(choose_universe_num, choose_universe_diff, status=ChooseSimUniNum.STATUS_RESTART))

        start_sim = StatusCombineOperationNode('开始挑战', SimUniStart(ctx))
        edges.append(StatusCombineOperationEdge2(choose_universe_diff, start_sim))
        edges.append(StatusCombineOperationEdge2(choose_universe_num, start_sim, status=ChooseSimUniNum.STATUS_CONTINUE))

        choose_path = StatusCombineOperationNode('选择命途', ChooseSimUniPath(ctx, SimUniPath.PROPAGATION))
        edges.append(StatusCombineOperationEdge2(start_sim, choose_path, status=SimUniStart.STATUS_RESTART))

        run_world = StatusCombineOperationNode('通关',
                                               SimUniRunWorld(ctx, 8,
                                                              bless_priority=bless_priority,
                                                              next_level_priority=next_level_priority)
                                               )
        edges.append(StatusCombineOperationEdge2(choose_path, run_world))
        edges.append(StatusCombineOperationEdge2(start_sim, run_world, status=ChooseSimUniNum.STATUS_CONTINUE))

        edges.append(StatusCombineOperationEdge2(run_world, choose_universe_num))

        super().__init__(ctx, op_name=gt(SIM_UNIVERSE.cn, 'ui'),
                         edges=edges,
                         run_record=get_record())

        self.current_uni_num: int = 8

    def _init_before_execute(self):
        super()._init_before_execute()

    def _on_uni_num_chosen(self, op_result: OperationResult):
        if op_result.success:
            self.current_uni_num = op_result.data

from typing import Optional, List

from basic.i18_utils import gt
from sr.app import AppDescription, register_app, AppRunRecord, Application2
from sr.const import phone_menu_const
from sr.context import Context
from sr.operation.combine import StatusCombineOperationEdge2, StatusCombineOperationNode
from sr.operation.unit.guide import GUIDE_TAB_3
from sr.operation.unit.guide.choose_guide_tab import ChooseGuideTab
from sr.operation.unit.guide.mission_transport import ChooseGuideMissionCategory, CATEGORY_ROGUE, ChooseGuideMission, \
    MISSION_SIM_UNIVERSE
from sr.operation.unit.menu.click_phone_menu_item import ClickPhoneMenuItem
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu
from sr.rogue import SimUniverseType
from sr.rogue.choose_sim_uni_num import ChooseSimUniNum
from sr.rogue.choose_sim_uni_type import ChooseSimUniType
from sr.rogue.choose_sum_uni_diff import ChooseSimUniDiff
from sr.rogue.start_sim_uni import StartSimUni

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

        choose_normal_universe = StatusCombineOperationNode('普通宇宙', ChooseSimUniType(ctx, SimUniverseType.NORMAL))
        edges.append(StatusCombineOperationEdge2(transport, choose_normal_universe))

        choose_universe_num = StatusCombineOperationNode('选择世界', ChooseSimUniNum(ctx, 7))
        edges.append(StatusCombineOperationEdge2(choose_normal_universe, choose_universe_num))

        choose_universe_diff = StatusCombineOperationNode('选择难度', ChooseSimUniDiff(ctx, 5))
        edges.append(StatusCombineOperationEdge2(choose_universe_num, choose_universe_diff))

        start_sim = StatusCombineOperationNode('开始挑战', StartSimUni(ctx))
        edges.append(StatusCombineOperationEdge2(choose_universe_diff, start_sim))

        super().__init__(ctx, op_name=gt(SIM_UNIVERSE.cn, 'ui'),
                         edges=edges)

    def _init_before_execute(self):
        super()._init_before_execute()

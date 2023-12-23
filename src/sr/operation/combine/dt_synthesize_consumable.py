from typing import List

from basic.i18_utils import gt
from sr.const import phone_menu_const
from sr.const.traing_mission_const import MISSION_SYNTHESIZE_CONSUMABLE
from sr.context import Context
from sr.operation.combine import StatusCombineOperation2, StatusCombineOperationNode, StatusCombineOperationEdge2
from sr.operation.unit.menu.click_phone_menu_item import ClickPhoneMenuItem
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu
from sr.operation.unit.menu.synthesize import DoSynthesize


class DtSynthesizeConsumable(StatusCombineOperation2):

    def __init__(self, ctx: Context):
        """
        每日实训 - 合成消耗品
        需要在大世界非战斗情况下使用
        :param ctx:
        """
        edges: List[StatusCombineOperationEdge2] = []

        open_menu = StatusCombineOperationNode('打开菜单', OpenPhoneMenu(ctx))
        choose_synthesize = StatusCombineOperationNode('打开【合成】', ClickPhoneMenuItem(ctx, phone_menu_const.SYNTHESIZE))
        edges.append(StatusCombineOperationEdge2(open_menu, choose_synthesize))

        do_synthesize = StatusCombineOperationNode('进行合成', DoSynthesize(ctx))
        edges.append(StatusCombineOperationEdge2(choose_synthesize, do_synthesize))  # 因为打开页就是消耗品 所以不需要选择菜单了

        back = StatusCombineOperationNode('返回菜单', OpenPhoneMenu(ctx))
        edges.append(StatusCombineOperationEdge2(do_synthesize, back))  # 因为打开页就是消耗品 所以不需要选择菜单了

        super().__init__(ctx,
                         op_name='%s %s' % (gt('实训任务', 'ui'), gt(MISSION_SYNTHESIZE_CONSUMABLE.id_cn, 'ui')),
                         edges=edges)

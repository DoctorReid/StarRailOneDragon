from basic.i18_utils import gt
from sr.const import phone_menu_const
from sr.context import Context
from sr.operation import StateOperation, StateOperationNode
from sr.operation.battle.choose_team import ChooseTeam
from sr.operation.common.back_to_normal_world_plus import BackToNormalWorldPlus
from sr.operation.unit.menu.click_phone_menu_item import ClickPhoneMenuItem
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu


class ChooseTeamInWorld(StateOperation):

    def __init__(self, ctx: Context, team_num: int):
        """
        在大世界中 根据队伍编号选择配队 选择后再返回大世界页面
        :param ctx: 上下文
        :param team_num: 队伍编号 从1开始
        """
        nodes = [
            StateOperationNode('返回大世界', op=BackToNormalWorldPlus(ctx)),
            StateOperationNode('菜单', op=OpenPhoneMenu(ctx)),
            StateOperationNode('编队', op=ClickPhoneMenuItem(ctx, phone_menu_const.TEAM_SETUP)),
            StateOperationNode('选择组队', op=ChooseTeam(ctx, team_num, on=True)),
            StateOperationNode('返回', op=BackToNormalWorldPlus(ctx)),
        ]
        super().__init__(ctx, op_name=gt('选择配队', 'ui'),
                         nodes=nodes)

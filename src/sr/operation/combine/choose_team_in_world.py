from typing import List

from basic.i18_utils import gt
from sr.const import phone_menu_const
from sr.context import Context
from sr.operation import Operation
from sr.operation.combine import CombineOperation
from sr.operation.unit.back_to_world import BackToWorld
from sr.operation.unit.battle.choose_team import ChooseTeam
from sr.operation.unit.menu.click_phone_menu_item import ClickPhoneMenuItem
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu


class ChooseTeamInWorld(CombineOperation):

    def __init__(self, ctx: Context, team_num: int):
        ops: List[Operation] = [
            BackToWorld(ctx),
            OpenPhoneMenu(ctx),
            ClickPhoneMenuItem(ctx, phone_menu_const.TEAM_SETUP),
            ChooseTeam(ctx, team_num, on=True),
        ]
        super().__init__(ctx, ops=ops, op_name=gt('选择配队', 'ui'))

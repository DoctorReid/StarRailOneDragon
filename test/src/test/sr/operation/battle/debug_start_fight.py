import unittest

import test
from sr.const import character_const
from sr.const.character_const import LUOCHA, TINGYUN, HERTA, DANHENGIMBIBITORLUNAE
from sr.context import get_context
from sr.operation.battle.start_fight import StartFightForElite
from sr.operation.unit.team import GetTeamMemberInWorld


class DebugStartFight(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

    def test_tl_get_technique_order(self):
        """
        逐光捡金里测试
        :return:
        """
        ctx = get_context()
        ctx.start_running()

        op = StartFightForElite(ctx, skip_point_check=True, skip_resurrection_check=True)
        op.execute()

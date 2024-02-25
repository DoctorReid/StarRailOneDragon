import unittest

import test
from sr.const import character_const
from sr.const.character_const import LUOCHA, TINGYUN, HERTA, DANHENGIMBIBITORLUNAE
from sr.context import get_context
from sr.operation.battle.choose_support import ChooseSupport
from sr.operation.battle.start_fight import StartFightForElite
from sr.operation.unit.team import GetTeamMemberInWorld


class TestChooseSupport(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

    def test_op(self):
        ctx = get_context()
        ctx.init_all()
        ctx.start_running()

        op = ChooseSupport(ctx, character_const.TOPAZNUMBY.id)
        op.execute()

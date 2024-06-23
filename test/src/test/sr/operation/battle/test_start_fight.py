import test
from sr.const import character_const
from sr.context.context import get_context
from sr.operation.battle.start_fight import StartFightForElite


class TestStartFight(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

    def test_get_technique_order(self):
        ctx = get_context()
        op = StartFightForElite(ctx,
                                character_list=[
                                         character_const.RUANMEI,
                                         character_const.TINGYUN,
                                         character_const.JINGLIU,
                                         character_const.LUOCHA
                                     ])
        op._get_character_list()
        op._get_technique_order()

        answer = [0, 1, 3, 2]
        self.assertEqual(len(answer), len(op.technique_order))

        for i in range(len(answer)):
            self.assertEqual(answer[i], op.technique_order[i])

import test
from sr.const import character_const
from sr.context.context import get_context
from sr.operation.battle.start_fight import StartFightForElite


class TestEnterFightInForgottenHall(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

        ctx = get_context()

        self.op = StartFightForElite(ctx)

    def test_get_technique_order(self):
        self.op.character_list = [
            character_const.CLARA,
            character_const.TINGYUN,
            # character_const.YUKONG,
            None,
            character_const.LUOCHA
        ]
        self.op._get_technique_order()
        print(self.op.technique_order)
        print('准备使用秘技 当前配队 %s' % [i.cn if i is not None else None for i in self.op.character_list])
import test
from sr.context.context import get_context
from sr.operation.battle.start_fight import StartFightForElite


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

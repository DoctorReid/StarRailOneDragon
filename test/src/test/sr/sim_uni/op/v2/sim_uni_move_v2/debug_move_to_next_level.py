import test
from sr.context import get_context
from sr.sim_uni.op.v2.sim_uni_move_v2 import MoveToNextLevelV2
from sr.sim_uni.sim_uni_const import SimUniLevelTypeEnum


class DebugSimUniRunRouteV2(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

    def test_op(self):
        ctx = get_context()
        ctx.start_running()

        op = MoveToNextLevelV2(ctx, SimUniLevelTypeEnum.ELITE.value)
        op.execute()

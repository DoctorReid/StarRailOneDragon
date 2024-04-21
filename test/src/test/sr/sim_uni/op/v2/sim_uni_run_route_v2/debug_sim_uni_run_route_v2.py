import test
from sr.const import character_const
from sr.context import get_context
from sr.image.sceenshot import screen_state
from sr.sim_uni.op.sim_uni_reward import SimUniReward
from sr.sim_uni.op.v2.sim_uni_run_route_v2 import SimUniRunCombatRouteV2


class DebugSimUniRunCombatRouteV2(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

    def test_op(self):
        ctx = get_context()
        ctx.init_all()
        ctx.start_running()
        ctx.sim_uni_info.world_num = 9
        ctx.team_info.character_list = [character_const.ACHERON]

        op = SimUniRunCombatRouteV2(ctx)
        op.execute()

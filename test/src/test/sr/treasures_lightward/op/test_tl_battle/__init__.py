import test
from sr.context import get_context
from sr.operation import Operation
from sr.screen_area.screen_treasures_lightward import ScreenTreasuresLightWard
from sr.treasures_lightward.op.tl_battle import TlAfterNodeFight
from sr.treasures_lightward.treasures_lightward_const import TreasuresLightwardTypeEnum


class TestTlBattle(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

    def test_op_after_node_fight(self):
        ctx = get_context()
        ctx.init_all()
        ctx.start_running()

        op = TlAfterNodeFight(ctx, TreasuresLightwardTypeEnum.FORGOTTEN_HALL)
        op.execute()

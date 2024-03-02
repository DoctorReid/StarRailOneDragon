import test
from sr.context import get_context
from sr.treasures_lightward.op.check_max_unlock_mission import CheckMaxUnlockMission
from sr.treasures_lightward.treasures_lightward_const import TreasuresLightwardTypeEnum


class TestCheckMaxUnlockMission(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

    def test_get_max_unlock_num(self):
        ctx = get_context()
        ctx.init_image_matcher()
        ctx.init_ocr_matcher()

        op = CheckMaxUnlockMission(ctx, TreasuresLightwardTypeEnum.PURE_FICTION)
        screen = self.get_test_image_new('pf.png')
        self.assertEquals(3, op.get_max_unlock_num(screen))

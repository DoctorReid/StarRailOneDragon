import test
from sr.app.treasures_lightward.treasures_lightward_app import TreasuresLightwardApp
from sr.const import character_const
from sr.context.context import get_context


class TestChooseTeamInForgottenHall(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

    def test_cal_team(self):
        ctx = get_context()
        ctx.init_image_matcher()

        app = TreasuresLightwardApp(ctx)

        app._cal_team_member(
            [
                [character_const.LIGHTNING, character_const.FIRE],
                [character_const.IMAGINARY, character_const.PHYSICAL]
            ]
        )


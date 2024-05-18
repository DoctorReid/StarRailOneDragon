import cv2

import test
from basic.img.os import get_debug_image
from sr.app.treasures_lightward.treasures_lightward_app import TreasuresLightwardApp
from sr.const import character_const
from sr.context import get_context
from sr.operation.unit.forgotten_hall.choose_team_in_fh import ChooseTeamInForgottenHall


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


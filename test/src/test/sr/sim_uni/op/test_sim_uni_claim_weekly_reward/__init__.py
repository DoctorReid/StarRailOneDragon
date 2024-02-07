import unittest

import test
from basic.img import cv2_utils
from sr.context import get_context
from sr.image.sceenshot import screen_state
from sr.sim_uni.op.sim_uni_claim_weekly_reward import SimUniClaimWeeklyReward
from sr.sim_uni.op.sim_uni_event import SimUniEvent
from test.sr.control.mock_controller import MockController


class TestSimUniClaimWeeklyReward(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

    def setUp(self) -> None:
        pass

    def test_check_reward_by_screen(self):
        ctx = get_context()
        ctx.init_image_matcher()
        ctx.init_ocr_matcher()
        ctx.controller = MockController(ctx.ocr)
        op = SimUniClaimWeeklyReward(ctx)

        screen = self.get_test_image_new('reward_icon.png')
        result = op._check_reward_by_screen(screen)
        self.assertEqual(result.status, SimUniClaimWeeklyReward.STATUS_WITH_REWARD)

    def test_claim_reward_by_screen(self):
        ctx = get_context()
        ctx.init_image_matcher()
        ctx.init_ocr_matcher()
        ctx.controller = MockController(ctx.ocr)
        op = SimUniClaimWeeklyReward(ctx)

        screen = self.get_test_image_new('claim_reward.png')
        result = op._claim_reward_by_screen(screen)
        self.assertTrue(result.is_success)

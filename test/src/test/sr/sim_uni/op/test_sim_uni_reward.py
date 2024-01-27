import unittest

import test
from sr.context import get_context
from sr.sim_uni.op.sim_uni_exit import SimUniExit
from sr.sim_uni.op.sim_uni_reward import SimUniReward


class TestSimUniReward(unittest.TestCase, test.SrTestBase):

    def setUp(self):
        test.SrTestBase.__init__(self, __file__)

    def test_get_reward_pos(self):
        ctx = get_context()
        ctx.init_ocr_matcher()

        op = SimUniReward(ctx, 1)
        screen = self.get_test_image('reward_right')
        pos = op._get_reward_pos(screen)
        self.assertIsNotNone(pos)
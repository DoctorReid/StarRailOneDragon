import unittest

import test
from sr.context import get_context
from sr.image.sceenshot import screen_state
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

    def test_screen_state(self):
        ctx = get_context()
        ctx.init_ocr_matcher()
        ctx.init_image_matcher()

        op = SimUniReward(ctx, 1)
        screen = self.get_test_image('reward_right')
        state = op._get_screen_state(screen)
        self.assertEqual(screen_state.ScreenState.SIM_REWARD.value, state)

    def test_op(self):
        ctx = get_context()
        ctx.start_running()

        op = SimUniReward(ctx, 2)
        # op._specified_start_node = op.edge_list[0].node_to
        op.execute()
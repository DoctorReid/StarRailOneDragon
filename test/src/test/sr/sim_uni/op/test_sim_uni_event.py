import unittest

import test
from sr.context import get_context
from sr.sim_uni.op.sim_uni_event import SimUniEventHerta, SimUniEvent


class TestSimUniEvent(unittest.TestCase, test.SrTestBase):

    def setUp(self):
        test.SrTestBase.__init__(self, __file__)

    def test_get_opt_list(self):
        ctx = get_context()
        ctx.init_ocr_matcher()
        ctx.init_image_matcher()
        op = SimUniEvent(ctx)

        screen = self.get_test_image('herta_normal_2')
        opt_list = op._get_opt_list(screen)
        self.assertEqual(4, len(opt_list))

        screen = self.get_test_image('event_no_confirm')
        opt_list = op._get_opt_list(screen)
        self.assertEqual(1, len(opt_list))

        screen = self.get_test_image('no_event')
        opt_list = op._get_opt_list(screen)
        self.assertEqual(0, len(opt_list))

        screen = self.get_test_image('herta_enhance')
        opt_list = op._get_opt_list(screen)
        self.assertEqual(1, len(opt_list))  # 暂时没有强化

    def test_get_screen_state(self):
        ctx = get_context()
        ctx.init_ocr_matcher()
        ctx.init_image_matcher()
        op = SimUniEvent(ctx)

        screen = self.get_test_image('event_no_confirm')
        state = op._get_screen_state(screen)
        self.assertIsNotNone(state)
        self.assertTrue('事件', state)

    def test_op_event(self):
        ctx = get_context()
        ctx.start_running()

        op = SimUniEvent(ctx)
        op.execute()

    def test_op_herta(self):
        ctx = get_context()
        ctx.start_running()

        op = SimUniEventHerta(ctx)
        op.execute()
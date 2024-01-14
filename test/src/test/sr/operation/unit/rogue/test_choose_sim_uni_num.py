import unittest

import test
from sr.context import get_context
from sr.sim_uni.op.choose_sim_uni_num import ChooseSimUniNum


class TestChooseSimUniNum(unittest.TestCase, test.SrTestBase):

    def setUp(self):
        test.SrTestBase.__init__(self, __file__)

        ctx = get_context()
        ctx.init_ocr_matcher()

        self.op = ChooseSimUniNum(ctx, 1, end_going=False)

    def test_get_current_num(self):
        screen = self.get_test_image('1')
        self.assertEqual(8, self.op._get_current_num(screen))

    def test_is_going(self):
        screen = self.get_test_image('1')
        self.assertTrue(self.op._is_going(screen))
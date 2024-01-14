import unittest

import test
from sr.context import get_context
from sr.image.sceenshot import screen_state


class TestOperation(unittest.TestCase, test.SrTestBase):

    def setUp(self):
        test.SrTestBase.__init__(self, __file__)

    def test_is_empty_to_close(self):
        ctx = get_context()
        ctx.init_ocr_matcher()

        screen = self.get_test_image('empty_to_close_1')
        self.assertTrue(screen_state.is_empty_to_close(screen, ctx.ocr))

        screen = self.get_test_image('sim_uni_finished')
        self.assertTrue(screen_state.is_empty_to_close(screen, ctx.ocr))

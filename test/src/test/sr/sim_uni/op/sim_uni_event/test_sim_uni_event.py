import unittest

import test
from basic.img import cv2_utils
from sr.context import get_context
from sr.image.sceenshot import screen_state
from sr.sim_uni.op.sim_uni_event import SimUniEvent


class TestSimUniEvent(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

    def test_get_opt_list(self):
        ctx = get_context()
        ctx.init_ocr_matcher()
        ctx.init_image_matcher()
        op = SimUniEvent(ctx)

        screen = self.get_test_image_new('herta_normal_2.png')
        opt_list = op._get_opt_list(screen)
        self.assertEqual(4, len(opt_list))

        screen = self.get_test_image_new('event_no_confirm.png')
        opt_list = op._get_opt_list(screen)
        self.assertEqual(1, len(opt_list))

        screen = self.get_test_image_new('no_event.png')
        opt_list = op._get_opt_list(screen)
        self.assertEqual(0, len(opt_list))

        screen = self.get_test_image_new('herta_enhance.png')
        opt_list = op._get_opt_list(screen)
        self.assertEqual(2, len(opt_list))

    def test_confirm_rect(self):
        ctx = get_context()
        ctx.init_ocr_matcher()
        ctx.init_image_matcher()
        op = SimUniEvent(ctx)

        screen = self.get_test_image_new('confirm_with_2_lines.png')
        opt_list = op._get_opt_list(screen)
        self.assertEqual(2, len(opt_list))
        part = cv2_utils.crop_image_only(screen, opt_list[1].confirm_rect)
        self.assertEqual('确定', ctx.ocr.ocr_for_single_line(part))

    def test_get_screen_state(self):
        ctx = get_context()
        ctx.init_ocr_matcher()
        ctx.init_image_matcher()
        op = SimUniEvent(ctx)

        screen = self.get_test_image_new('event_no_confirm.png')
        state = op._get_screen_state(screen)
        self.assertTrue('事件', state)

        screen = self.get_test_image_new('choose_bless.png')
        state = op._get_screen_state(screen)
        self.assertTrue(screen_state.ScreenState.SIM_BLESS.value, state)

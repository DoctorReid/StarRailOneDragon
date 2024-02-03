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

        screen = self.get_test_image('event_get_curio')
        self.assertTrue(screen_state.is_empty_to_close(screen, ctx.ocr))

        screen = self.get_test_image('event_lose_money')
        self.assertTrue(screen_state.is_empty_to_close(screen, ctx.ocr))

        screen = self.get_test_image('sim_uni_reward')
        self.assertTrue(screen_state.is_empty_to_close(screen, ctx.ocr))

    def test_get_ui_title(self):
        ctx = get_context()
        ctx.init_ocr_matcher()

        screen = self.get_test_image('empty_to_close_1')
        self.assertEqual(0, len(screen_state.get_ui_title(screen, ctx.ocr)))

    def test_get_tp_battle_screen_state(self):
        ctx = get_context()
        ctx.init_ocr_matcher()
        ctx.init_image_matcher()

        screen = self.get_test_image('tp_battle_fail')
        state = screen_state.get_tp_battle_screen_state(screen, ctx.im, ctx.ocr,
                                                        in_world=True,
                                                        battle_success=True,
                                                        battle_fail=True)
        self.assertEqual(screen_state.ScreenState.BATTLE_FAIL.value, state)

        screen = self.get_test_image('tp_battle_success_1')
        state = screen_state.get_tp_battle_screen_state(screen, ctx.im, ctx.ocr,
                                                        in_world=True,
                                                        battle_success=True,
                                                        battle_fail=True)
        self.assertEqual(screen_state.ScreenState.TP_BATTLE_SUCCESS.value, state)

        screen = self.get_test_image('tp_battle_success_2')
        state = screen_state.get_tp_battle_screen_state(screen, ctx.im, ctx.ocr,
                                                        in_world=True,
                                                        battle_success=True,
                                                        battle_fail=True)
        self.assertEqual(screen_state.ScreenState.TP_BATTLE_SUCCESS.value, state)

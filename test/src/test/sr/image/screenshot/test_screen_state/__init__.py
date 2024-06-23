import test
from sr.context.context import get_context
from sr.image.sceenshot import screen_state
from sr.image.sceenshot.screen_state_enum import ScreenState


class TestOperation(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

    def test_is_empty_to_close(self):
        ctx = get_context()
        ctx.init_ocr_matcher()

        screen = self.get_test_image_new('empty_to_close_1.png')
        self.assertTrue(screen_state.is_empty_to_close(screen, ctx.ocr))

        screen = self.get_test_image_new('sim_uni_finished.png')
        self.assertTrue(screen_state.is_empty_to_close(screen, ctx.ocr))

        screen = self.get_test_image_new('event_get_curio.png')
        self.assertTrue(screen_state.is_empty_to_close(screen, ctx.ocr))

        screen = self.get_test_image_new('event_lose_money.png')
        self.assertTrue(screen_state.is_empty_to_close(screen, ctx.ocr))

        screen = self.get_test_image_new('sim_uni_reward.png')
        self.assertTrue(screen_state.is_empty_to_close(screen, ctx.ocr))

    def test_get_tp_battle_screen_state(self):
        ctx = get_context()
        ctx.init_ocr_matcher()
        ctx.init_image_matcher()

        screen = self.get_test_image_new('tp_battle_fail.png')
        state = screen_state.get_tp_battle_screen_state(screen, ctx.im, ctx.ocr,
                                                        in_world=True,
                                                        battle_success=True,
                                                        battle_fail=True)
        self.assertEqual(ScreenState.BATTLE_FAIL.value, state)

        screen = self.get_test_image_new('tp_battle_success_1.png')
        state = screen_state.get_tp_battle_screen_state(screen, ctx.im, ctx.ocr,
                                                        in_world=True,
                                                        battle_success=True,
                                                        battle_fail=True)
        self.assertEqual(ScreenState.TP_BATTLE_SUCCESS.value, state)

        screen = self.get_test_image_new('tp_battle_success_2.png')
        state = screen_state.get_tp_battle_screen_state(screen, ctx.im, ctx.ocr,
                                                        in_world=True,
                                                        battle_success=True,
                                                        battle_fail=True)
        self.assertEqual(ScreenState.TP_BATTLE_SUCCESS.value, state)

    def test_get_ui_title(self):
        ctx = get_context()
        ctx.init_ocr_matcher()

        screen = self.get_test_image_new('empty_to_close_1.png')
        self.assertEqual(0, len(screen_state.get_ui_title(screen, ctx.ocr)))

import test
from sr.context import get_context
from sr.operation import Operation
from sr.screen_area.screen_treasures_lightward import ScreenTreasuresLightWard


class TestScreenTreasuresLightWard(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

    def test_quick_pass(self):
        ctx = get_context()
        ctx.init_ocr_matcher()

        op = Operation(ctx)

        screen = self.get_test_image_new('quick_pass.png')
        check_area_list = [
            ScreenTreasuresLightWard.AFTER_BATTLE_QUICK_PASS_TITLE.value,
            ScreenTreasuresLightWard.AFTER_BATTLE_QUICK_PASS_CONFIRM.value
        ]
        for area in check_area_list:
            self.assertTrue(op.find_area(area, screen))

        screen = self.get_test_image_new('quick_pass_empty.png')
        check_area_list = [
            ScreenTreasuresLightWard.AFTER_BATTLE_QUICK_PASS_EMPTY.value,
        ]
        for area in check_area_list:
            self.assertTrue(op.find_area(area, screen))

    def test_normal_world(self):
        ctx = get_context()
        ctx.init_image_matcher()
        ctx.init_ocr_matcher()

        op = Operation(ctx)

        screen = self.get_test_image_new('normal_world.png')
        check_area_list = [
            ScreenTreasuresLightWard.EXIT_BTN.value,
        ]
        for area in check_area_list:
            self.assertTrue(op.find_area(area, screen))


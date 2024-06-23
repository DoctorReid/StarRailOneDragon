import test
from sr.context.context import get_context
from sr.sim_uni.op.sim_uni_choose_bless import SimUniUpgradeBless


class TestSimUniUpgradeBless(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

    def test_get_left_num(self):
        ctx = get_context()
        ctx.init_ocr_matcher()
        op = SimUniUpgradeBless(ctx)

        screen = self.get_test_image_new('upgrade.png')
        self.assertEqual(189, op._get_left_num(screen))

    def test_get_bless_pos_list(self):
        ctx = get_context()
        ctx.init_ocr_matcher()
        ctx.init_image_matcher()
        op = SimUniUpgradeBless(ctx)

        screen = self.get_test_image_new('upgrade.png')
        op.left_num = 189

        op._get_bless_pos_list(screen)
        self.assertEqual(1, len(op.upgrade_list))
        self.assertEqual(160, op.upgrade_list[0].data)

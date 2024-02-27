import test
from sr.context import get_context
from sr.sim_uni.op.choose_sim_uni_num import ChooseSimUniNum


class TestChooseSimUniNum(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

    def test_get_current_num(self):
        ctx = get_context()
        ctx.init_ocr_matcher()

        op = ChooseSimUniNum(ctx, 6)

        screen = self.get_test_image_new('num2.png')
        op.num = 6
        self.assertEqual(6, op._get_current_num(screen))

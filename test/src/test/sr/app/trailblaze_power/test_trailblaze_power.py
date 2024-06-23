import test
from sr.app.trailblaze_power.trailblaze_power_app import TrailblazePower
from sr.context.context import get_context


class TestTrailblazePower(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

    def test_get_sim_uni_power_and_qty(self):
        ctx = get_context()
        ctx.init_ocr_matcher()

        op = TrailblazePower(ctx)

        screen = self.get_test_image_new('sim_uni_power.png')
        x, y = op._get_power_and_qty(screen)

        self.assertEqual(92, x)
        self.assertEqual(9, y)

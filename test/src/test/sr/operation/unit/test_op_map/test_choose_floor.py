import cv2

import test
from basic import cal_utils, Point
from sr.context.context import get_context
from sr.operation.unit.op_map import ChooseFloor


class TestChooseFloor(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

    def test_get_target_floor_pos(self):
        ctx = get_context()
        ctx.init_ocr_matcher()
        op = ChooseFloor(ctx, -2)

        screen = self.get_test_image_new('sub_floor_b2.png')
        op.sub_region = True
        pos = op.get_target_floor_pos(screen)
        self.assertTrue(cal_utils.distance_between(pos, Point(78, 958)) < 5)

        screen = self.get_test_image_new('sub_floor_b2_active.png')
        op.sub_region = True
        pos = op.get_target_floor_pos(screen)
        self.assertTrue(cal_utils.distance_between(pos, Point(78, 958)) < 5)

        cv2.destroyAllWindows()

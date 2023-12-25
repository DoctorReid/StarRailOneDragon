import unittest

import test
from basic import cal_utils, Point
from sr.context import get_context
from sr.operation.unit.store.click_store_item import ClickStoreItem


class TestGetTeamMemberInWorld(unittest.TestCase, test.SrTestBase):

    def setUp(self):
        test.SrTestBase.__init__(self, __file__)

        ctx = get_context()
        ctx.init_ocr_matcher()

        self.op = ClickStoreItem(ctx, '逾期未取的贵重邮包', 0.5)

    def test_parcel(self):
        """逾期未取的贵重邮包"""
        screen = self._get_test_image('parcel')
        best_result = self.op._get_item_pos(screen)
        self.assertIsNotNone(best_result)
        self.assertTrue(cal_utils.distance_between(Point(430, 640), best_result.center) < 20)

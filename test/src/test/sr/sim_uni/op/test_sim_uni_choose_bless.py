import time
import unittest
from typing import List

import test
from sr.context import get_context
from sr.sim_uni.op.sim_uni_choose_bless import SimUniChooseBless
from sr.sim_uni.sim_uni_const import SimUniBless, SimUniBlessEnum


class TestChooseSimUniNum(unittest.TestCase, test.SrTestBase):

    def setUp(self):
        test.SrTestBase.__init__(self, __file__)

        ctx = get_context()
        ctx.init_ocr_matcher()
        self.op = SimUniChooseBless(ctx, None)

    def test_get_bless(self):
        """
        有3个祝福
        :return:
        """
        screen = self.get_test_image('1')

        st = time.time()
        bless_list = self.op._get_bless_pos(screen)
        # bless_list = self.op._get_bless_pos_v2(screen)
        # bless_list = self.op._get_bless_pos_v3(screen, SimUniChooseBless.BLESS_3_RECT_LIST)
        print(time.time() - st)

        answer: List[SimUniBless] = [
            SimUniBlessEnum.BLESS_06_023.value,
            SimUniBlessEnum.BLESS_05_017.value,
            SimUniBlessEnum.BLESS_04_022.value
        ]

        self.assertEqual(len(answer), len(bless_list))
        for i in range(len(answer)):
            self.assertEqual(answer[i], bless_list[i].data)

    def test_get_bless_2(self):
        """
        只有2个祝福的情况
        :return:
        """
        screen = self.get_test_image('3')

        bless_list = self.op._get_bless_pos(screen)

        answer: List[SimUniBless] = [
            SimUniBlessEnum.BLESS_07_024.value,
            SimUniBlessEnum.BLESS_04_019.value,
        ]

        self.assertEqual(len(answer), len(bless_list))
        for i in range(len(answer)):
            self.assertEqual(answer[i], bless_list[i].data)

    def test_get_bless_before_start(self):
        """
        楼层开始前的情况
        :return:
        """
        screen = self.get_test_image('before_level')

        ctx = get_context()
        ctx.init_ocr_matcher()

        op = SimUniChooseBless(ctx, None, before_level_start=True )

        bless_list = op._get_bless_pos(screen)

        answer: List[SimUniBless] = [
            SimUniBlessEnum.BLESS_00_001.value,
            SimUniBlessEnum.BLESS_00_002.value,
            SimUniBlessEnum.BLESS_00_003.value,
        ]

        self.assertEqual(len(answer), len(bless_list))
        for i in range(len(answer)):
            self.assertEqual(answer[i], bless_list[i].data)

    def test_can_reset(self):
        screen = self.get_test_image('can_reset_1')
        self.assertTrue(self.op._can_reset(screen))

        screen = self.get_test_image('cant_reset_1')
        self.assertFalse(self.op._can_reset(screen))

        screen = self.get_test_image('cant_reset_2')
        self.assertFalse(self.op._can_reset(screen))

    def test_op(self):
        ctx = get_context()
        ctx.start_running()

        op = SimUniChooseBless(ctx, None, before_level_start=True)
        op.execute()

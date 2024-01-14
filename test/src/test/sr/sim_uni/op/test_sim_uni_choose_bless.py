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

        bless_list = self.op._get_bless_pos(screen)

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


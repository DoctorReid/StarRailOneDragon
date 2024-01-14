import unittest
from typing import List

import test
from sr.context import get_context
from sr.sim_uni.op.sim_uni_choose_curio import SimUniChooseCurio
from sr.sim_uni.sim_uni_const import SimUniCurioEnum, SimUniCurio


class TestChooseSimUniCurio(unittest.TestCase, test.SrTestBase):

    def setUp(self):
        test.SrTestBase.__init__(self, __file__)

    def test_get_curio_pos(self):
        ctx = get_context()
        ctx.init_ocr_matcher()
        screen = self.get_test_image('1')

        op = SimUniChooseCurio(ctx)

        curio_list = op._get_curio_pos(screen)

        self.assertEqual(3, len(curio_list))

        answer: List[SimUniCurio] = [
            SimUniCurioEnum.CURIO_011.value,
            SimUniCurioEnum.CURIO_024.value,
            SimUniCurioEnum.CURIO_022.value,
        ]
        for i in range(3):
            self.assertEqual(answer[i].name, curio_list[i].data.name)

    def test_op(self):
        ctx = get_context()
        ctx.start_running()

        op = SimUniChooseCurio(ctx)
        op.execute()

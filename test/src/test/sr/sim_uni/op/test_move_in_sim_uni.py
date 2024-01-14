import unittest

import test
from sr.context import get_context
from sr.sim_uni.op.sim_uni_choose_bless import SimUniChooseBless
from sr.sim_uni.op.move_in_sim_uni import MoveToNextLevel
from sr.sim_uni.sim_uni_const import SimUniLevelTypeEnum
from sr.sim_uni.sim_uni_priority import SimUniNextLevelPriority


class TestChooseSimUniNum(unittest.TestCase, test.SrTestBase):

    def setUp(self):
        test.SrTestBase.__init__(self, __file__)

        ctx = get_context()
        ctx.init_ocr_matcher()
        self.op = SimUniChooseBless(ctx, None)

    def test_get_next_level_type(self):
        ctx = get_context()
        ctx.init_image_matcher()
        op = MoveToNextLevel(ctx, None)

        screen = self.get_test_image('next_level_battle_event')

        result = op._get_next_level_type(screen)
        self.assertEqual(2, len(result))

        self.assertEqual(SimUniLevelTypeEnum.COMBAT.value, result[0].data)
        self.assertEqual(SimUniLevelTypeEnum.EVENT.value, result[1].data)

    def test_next_level_can_interact(self):
        ctx = get_context()
        ctx.init_image_matcher()
        op = MoveToNextLevel(ctx, None)

        screen = self.get_test_image('next_level_can_interact')

        result = op._can_interact(screen)
        self.assertTrue(result, msg='当前应该可交互')

    def test_move_towards_next_level(self):
        ctx = get_context()
        ctx.start_running()

        op = MoveToNextLevel(ctx, SimUniNextLevelPriority(SimUniLevelTypeEnum.COMBAT.value.type_id))
        op.execute()

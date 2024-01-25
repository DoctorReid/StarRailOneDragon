import unittest

import test
from sr.context import get_context
from sr.sim_uni.op.move_in_sim_uni import MoveToNextLevel
from sr.sim_uni.sim_uni_const import SimUniLevelTypeEnum


class TestMoveToNextLevel(unittest.TestCase, test.SrTestBase):

    def setUp(self):
        test.SrTestBase.__init__(self, __file__)

    def test_get_next_level_type(self):
        ctx = get_context()
        ctx.init_image_matcher()

        screen = self.get_test_image('next_level_battle_event')

        result = MoveToNextLevel.get_next_level_type(screen, ctx.ih)
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

        op = MoveToNextLevel(ctx, None)
        op.execute()

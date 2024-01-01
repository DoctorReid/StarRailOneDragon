import unittest

import test
from sr.app.routine.forgotten_hall_app import ForgottenHallApp
from sr.const import character_const
from sr.context import get_context
from sr.operation.unit.forgotten_hall.choose_team_in_fh import ChooseTeamInForgottenHall


class TestChooseTeamInForgottenHall(unittest.TestCase, test.SrTestBase):

    def setUp(self):
        test.SrTestBase.__init__(self, __file__)

        ctx = get_context()
        ctx.init_image_matcher()

        app = ForgottenHallApp(ctx)

        self.op = ChooseTeamInForgottenHall(ctx, app._cal_team_member)

    def test_get_all_node_combat_types(self):
        """
        1.6版本更新
        """
        screen = self.get_test_image('1')
        node_combat_types = self.op._get_all_node_combat_types(screen)

        self.assertEqual(2, len(node_combat_types))

        node1 = node_combat_types[0]
        self.assertEqual(2, len(node1))
        self.assertEqual(character_const.ICE, node1[0])
        self.assertEqual(character_const.FIRE, node1[1])

        node2 = node_combat_types[1]
        self.assertEqual(2, len(node2))
        self.assertEqual(character_const.QUANTUM, node2[0])
        self.assertEqual(character_const.WIND, node2[1])

import unittest

import test
from sr.context import get_context
from sr.operation.unit.battle.choose_team import ChooseTeam


class TestGetTeamMemberInWorld(unittest.TestCase, test.SrTestBase):

    def setUp(self):
        test.SrTestBase.__init__(self, __file__)

        ctx = get_context()
        ctx.init_ocr_matcher()

        self.op = ChooseTeam(ctx, team_num=1)

    def test_get_all_num_pos(self):
        team_nums_in_img = [[1, 2, 3, 4, 5, 6, 7], [2, 3, 4, 5, 6, 7, 8], [3, 4, 5, 6, 7, 8, 9]]
        for i in range(1, 4):
            screen = self.get_test_image(str(i))
            team_nums = self.op.get_all_num_pos(screen)
            self.assertEquals(len(team_nums_in_img[i - 1]), len(team_nums))

            for num in team_nums.keys():
                self.assertTrue(num in team_nums_in_img[i - 1])

    def test_in_secondary_ui(self):
        for i in range(1, 4):
            screen = self.get_test_image(str(i))
            self.assertTrue(self.op.in_secondary_ui(screen))

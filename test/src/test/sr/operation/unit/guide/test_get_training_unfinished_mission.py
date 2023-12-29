import unittest
from typing import List

import test
from basic import cal_utils, Point
from basic.img import MatchResult
from sr.const.traing_mission_const import MISSION_DAILY_MISSION, MISSION_PATH, MISSION_USE_CONSUMABLE, \
    MISSION_FORGOTTEN_HALL, DailyTrainingMission, MISSION_DESTRUCTIBLE_OBJECTS, MISSION_DEFEAT_ENEMY, \
    MISSION_WEAKNESS_BREAK
from sr.context import get_context
from sr.operation.unit.guide.get_training_unfinished_mission import GetTrainingUnfinishedMission


class TestGetTrainingUnfinishedMission(unittest.TestCase, test.SrTestBase):

    def setUp(self):
        test.SrTestBase.__init__(self, __file__)

        ctx = get_context()
        ctx.init_ocr_matcher()

        self.op = GetTrainingUnfinishedMission(ctx)

        self.go_points: List[List[Point]] = [
            [Point(433, 830), Point(772, 830), Point(1109, 830), Point(1442, 830)],
            [Point(513, 830), Point(834, 830), Point(1164, 830), Point(1504, 830)],
        ]
        self.missions: List[List[DailyTrainingMission]] = [
            [MISSION_DAILY_MISSION, MISSION_PATH, MISSION_USE_CONSUMABLE, MISSION_FORGOTTEN_HALL],
            [MISSION_PATH, MISSION_WEAKNESS_BREAK, MISSION_DEFEAT_ENEMY, MISSION_DESTRUCTIBLE_OBJECTS],
        ]

    def test_get_go_pos(self):
        for pic in range(len(self.go_points)):
            screen = self.get_test_image(str(pic + 1))
            go_points = self.go_points[pic]
            go_pos_list = self.op._get_go_pos(screen)
            self.assertEquals(4, len(go_pos_list))
            for i in range(4):
                self.assertTrue(cal_utils.distance_between(go_pos_list[i].center, go_points[i]) < 20)

    def test_get_mission(self):
        for pic in range(len(self.go_points)):
            screen = self.get_test_image(str(pic + 1))
            go_points = self.go_points[pic]
            missions = self.missions[pic]

            for i in range(4):
                p = go_points[i]
                m = MatchResult(1, p.x - 10, p.y - 10, 10, 10)
                self.assertTrue(missions[i], self.op._get_mission(screen, m))

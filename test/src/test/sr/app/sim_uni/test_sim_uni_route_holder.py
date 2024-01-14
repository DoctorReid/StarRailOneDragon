import unittest

import test
from sr.app.sim_uni.sim_uni_route_holder import match_best_sim_uni_route
from sr.sim_uni.sim_uni_route import SimUniRoute


class TestSimUniRouteHolder(unittest.TestCase, test.SrTestBase):

    def setUp(self):
        test.SrTestBase.__init__(self, __file__)

    def test_match_best_08_03_01(self):
        self._match_best(8, 3, 1)

    def _match_best(self, uni_num: int, level: int, idx: int):
        mm = self.get_test_image('match_%02d_%02d_%02d' % (uni_num, level, idx))
        route = match_best_sim_uni_route(uni_num, level, mm)
        self.assertIsNotNone(route)
        self.assertEqual(SimUniRoute.get_uid(uni_num, level, idx), route.uid)

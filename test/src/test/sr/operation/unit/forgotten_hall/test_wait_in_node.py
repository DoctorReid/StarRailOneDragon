import unittest

import test
from sr.context import get_context
from sr.operation.battle.start_fight import StartFightForElite


class TestEnterFightInForgottenHall(unittest.TestCase, test.SrTestBase):

    def setUp(self):
        test.SrTestBase.__init__(self, __file__)

        ctx = get_context()

        self.op = StartFightForElite(ctx)
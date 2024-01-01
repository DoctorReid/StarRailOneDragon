import unittest

import test
from sr.context import get_context
from sr.operation.unit.forgotten_hall.enter_fight_in_fh import EnterFightInForgottenHall


class TestEnterFightInForgottenHall(unittest.TestCase, test.SrTestBase):

    def setUp(self):
        test.SrTestBase.__init__(self, __file__)

        ctx = get_context()

        self.op = EnterFightInForgottenHall(ctx)
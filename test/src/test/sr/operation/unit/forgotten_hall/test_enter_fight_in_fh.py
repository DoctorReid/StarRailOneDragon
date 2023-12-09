import unittest
import test
from sr.const import character_const
from sr.context import get_context
from sr.operation.unit.forgotten_hall.enter_fight_in_fh import EnterFightInForgottenHall


class TestEnterFightInForgottenHall(unittest.TestCase, test.SrTestBase):

    def setUp(self):
        test.SrTestBase.__init__(self, __file__)

        ctx = get_context()

        self.op = EnterFightInForgottenHall(ctx)

    def test_get_technique_order(self):
        self.op.character_list = [
            character_const.CLARA,
            character_const.TINGYUN,
            character_const.YUKONG,
            character_const.LUOCHA
        ]
        self.op._get_technique_order()
        print(self.op.technique_order)
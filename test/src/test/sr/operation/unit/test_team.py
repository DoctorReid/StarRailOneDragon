import unittest

import test
from sr.context import get_context
from sr.operation.unit.team import SwitchMember


class TestTeam(unittest.TestCase, test.SrTestBase):

    def setUp(self):
        test.SrTestBase.__init__(self, __file__)

    def test_switch_op(self):
        ctx = get_context()
        ctx.start_running()

        op = SwitchMember(ctx, 1)
        op.execute()

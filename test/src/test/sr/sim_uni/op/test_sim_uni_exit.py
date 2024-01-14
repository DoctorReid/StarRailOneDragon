import unittest

import test
from sr.context import get_context
from sr.sim_uni.op.sim_uni_event import SimUniEventHerta, SimUniEvent
from sr.sim_uni.op.sim_uni_exit import SimUniExit


class TestSimUniEvent(unittest.TestCase, test.SrTestBase):

    def setUp(self):
        test.SrTestBase.__init__(self, __file__)

    def test_op(self):
        ctx = get_context()
        ctx.start_running()

        op = SimUniExit(ctx)
        op.execute()

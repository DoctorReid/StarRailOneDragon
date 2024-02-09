import unittest

import test
from sr.context import get_context
from sr.sim_uni.op.sim_uni_exit import SimUniExit


class TestSimUniEvent(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

    def test_op(self):
        ctx = get_context()
        ctx.start_running()

        op = SimUniExit(ctx)
        op.execute()

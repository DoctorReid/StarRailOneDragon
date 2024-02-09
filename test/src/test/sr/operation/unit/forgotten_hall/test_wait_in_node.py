import unittest

import test
from sr.context import get_context
from sr.operation.battle.start_fight import StartFightForElite


class TestEnterFightInForgottenHall(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

        ctx = get_context()

        self.op = StartFightForElite(ctx)
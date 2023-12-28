import unittest

import test
from sr.context import get_context


class TestGetTeamMemberInWorld(unittest.TestCase, test.SrTestBase):

    def setUp(self):
        test.SrTestBase.__init__(self, __file__)

        ctx = get_context()

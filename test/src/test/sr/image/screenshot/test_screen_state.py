import unittest

import test
from sr.context import get_context
from sr.image.sceenshot import screen_state


class TestOperation(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

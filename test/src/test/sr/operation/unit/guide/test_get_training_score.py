import unittest

import test
from sr.context import get_context
from sr.operation.unit.guide.get_training_score import GetTrainingScore


class TestGetTrainingScore(unittest.TestCase, test.SrTestBase):

    def setUp(self):
        test.SrTestBase.__init__(self, __file__)

        ctx = get_context()
        ctx.init_ocr_matcher()

        self.op = GetTrainingScore(ctx)

    def test_get_score(self):
        screen = self._get_test_image('1')
        self.assertEquals(200, self.op._get_score(screen))
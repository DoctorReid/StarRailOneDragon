import unittest

import test
from sr.context import get_context
from sr.operation.unit.guide.get_training_score import GetTrainingScore


class TestGetTrainingScore(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

        ctx = get_context()
        ctx.init_ocr_matcher()

        self.op = GetTrainingScore(ctx)

    def test_get_score(self):
        screen = self.get_test_image_new('1.png')
        self.assertEquals(200, self.op._get_score(screen))
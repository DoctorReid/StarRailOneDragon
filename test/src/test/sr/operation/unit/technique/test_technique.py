import test
from sr.context import get_context
from sr.operation.unit.technique import pc_can_use_technique


class TestTechnique(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

    def test_pc_can_use_technique(self):
        ctx = get_context()
        ctx.init_ocr_matcher()

        screen = self.get_test_image_new('pc_can_use_tech.png')
        self.assertTrue(pc_can_use_technique(screen, ctx.ocr, 'e'))

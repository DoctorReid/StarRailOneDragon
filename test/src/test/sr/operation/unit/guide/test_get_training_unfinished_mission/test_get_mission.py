import test
from basic.img.os import get_debug_image
from sr.context import get_context
from sr.operation.unit.guide.get_training_unfinished_mission import GetTrainingUnfinishedMission


class TestGetTrainingUnfinishedMission(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

    def test_get_mission_list(self):
        ctx = get_context()
        ctx.init_ocr_matcher()

        op = GetTrainingUnfinishedMission(ctx)

        screen = get_debug_image('_1718504557537')
        self.save_test_image(screen, '1.png')
        screen = self.get_test_image_new('1.png')

        missions = op.get_mission_list(screen)
        print(missions)
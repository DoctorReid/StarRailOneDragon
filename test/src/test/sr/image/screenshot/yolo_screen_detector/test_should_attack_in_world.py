import time

import test
from sr.context.context import get_context


class TestOperation(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

    def test_sync(self):
        ctx = get_context()
        ctx.init_yolo_detector()

        screen = self.get_test_image_new('1.png')
        self.assertTrue(ctx.yolo_detector.should_attack_in_world(screen, time.time()))

    def test_async(self):
        ctx = get_context()
        ctx.init_yolo_detector()

        screen = self.get_test_image_new('1.png')
        for i in range(2):
            submit, _ = ctx.yolo_detector.detect_should_attack_in_world_async(screen, time.time())
            if i == 0:
                self.assertTrue(submit)
            else:
                self.assertFalse(submit)

        time.sleep(0.1)
        self.assertTrue(ctx.yolo_detector.should_attack_in_world_last_result(time.time()))

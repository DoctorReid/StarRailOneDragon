import cv2

import test
from basic.img import cv2_utils
from basic.img.os import get_debug_image
from sr.context import get_context
from sryolo.detector import draw_detections


class DebugDetector(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

    def test_debug_image(self):
        ctx = get_context()

        img = get_debug_image('2')
        results = ctx._sim_uni_yolo.detect(img, conf=0.5)
        cv2_utils.show_image(draw_detections(img, results), wait=0)
        cv2.destroyAllWindows()
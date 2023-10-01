import cv2

from basic.img.os import get_test_image
from sr import constants
from sr.constants.map import TransportPoint
from sr.image.cv2_matcher import CvImageMatcher
from sr.image.image_holder import ImageHolder
from sr.map_cal import MapCalculator


def _print_tp_pos(tp: TransportPoint):
    lm = ih.get_large_map(tp.region, map_type='origin')
    lm_info = mc.analyse_large_map(lm)

    screen = get_test_image('%s-%s-%s' % (tp.planet.id, tp.region.id, tp.id), sub_dir='tp')
    mm = mc.cut_mini_map(screen)
    mm_info = mc.analyse_mini_map(mm)

    print(mc.cal_character_pos_with_scale(lm_info, mm_info, show=True))
    cv2.waitKey(0)


if __name__ == '__main__':
    ih = ImageHolder()
    im = CvImageMatcher()
    mc = MapCalculator(im=im)
    _print_tp_pos(constants.map.P01_R03_TP01_KZZXW)
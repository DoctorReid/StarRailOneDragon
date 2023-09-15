import os

import cv2

import test_utils
from basic.img import cv2_utils, ImageMatcher
from basic.img.cv2_matcher import CvImageMatcher
from sr.map_cal import MapCalculator

mc = MapCalculator()


def _test_little_map():
    image = cv2_utils.read_image_with_alpha(test_utils.get_test_image('game1.png'))
    mc.cal_little_map_pos(image)
    little_map = mc.cut_little_map(image)
    cv2_utils.show_image(little_map)


def _test_little_map_arrow():
    image = cv2_utils.read_image_with_alpha(test_utils.get_test_image('game1.png'))
    arrow_1 = mc.cut_little_map_arrow(image)
    cv2_utils.show_image(arrow_1)
    mc.cal_little_map_pos(image)
    arrow_2 = mc.cut_little_map_arrow(image)
    cv2_utils.show_image(arrow_2)


def _test_get_direction_by_screenshot():
    matcher: ImageMatcher = CvImageMatcher()
    matcher.load_template('loc_arrow', test_utils.get_test_image('loc_arrow.png'))
    game = cv2_utils.read_image_with_alpha(test_utils.get_test_image('game1.png'))
    mc.cal_little_map_pos(game)
    print(mc.get_direction_by_screenshot(game, matcher, show_match_result=True))


if __name__ == '__main__':
    _test_get_direction_by_screenshot()
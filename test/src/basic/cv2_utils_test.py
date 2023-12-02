import cv2
import numpy as np

import basic.cal_utils
from basic import Rect
from basic.img import cv2_utils
from basic.img.os import get_debug_image
from sr.const.character_const import CHARACTER_LIST
from sr.image.image_holder import ImageHolder


def _test_get_angle_by_pts():
    angle = basic.cal_utils.get_angle_by_pts((0, 0), (1, 1))
    print(angle)
    assert abs(45 - angle) < 1e-5


def _test_ellipse():
    radio_mask = np.zeros((50, 50), dtype=np.uint8)
    cv2.ellipse(radio_mask, (25, 25), (10, 10), 0, 200, 300, 255, -1)
    cv2_utils.show_image(radio_mask, win_name='1')

    radio_mask = np.zeros((50, 50), dtype=np.uint8)
    cv2.ellipse(radio_mask, (25, 25), (10, 10), 0, -90, 90, 255, -1)
    cv2_utils.show_image(radio_mask, win_name='2')

    radio_mask = np.zeros((50, 50), dtype=np.uint8)
    cv2.ellipse(radio_mask, (25, 25), (10, 10), 0, 270, 90+360, 255, -1)
    cv2_utils.show_image(radio_mask, win_name='3')

    cv2.waitKey(0)


def _test_feature_match_for_multi():
    ih = ImageHolder()
    screen = get_debug_image('_1701498513655')
    # screen = get_debug_image('_1701500587965')

    part, _ = cv2_utils.crop_image(screen, Rect(70, 160, 520, 940))
    source_kps, source_desc = cv2_utils.feature_detect_and_compute(part)
    cv2_utils.show_image(part)

    for c in CHARACTER_LIST:
        template = ih.get_character_avatar_template(c.id)
        match_result_list = cv2_utils.feature_match_for_multi(
            source_kps, source_desc,
            template.kps, template.desc,
            template.origin.shape[1], template.origin.shape[0],
            knn_distance_percent=0.7)

        for r in match_result_list:
            r.x += 70
            r.y += 160

        if len(match_result_list) > 0:
            print(c.id)
            cv2_utils.show_image(screen, match_result_list, wait=0)


def _test_feature_match_for_one():
    ih = ImageHolder()
    screen = get_debug_image('_1701498513655')
    # screen = get_debug_image('_1701500587965')

    part, _ = cv2_utils.crop_image(screen, Rect(70, 160, 520, 940))
    source_kps, source_desc = cv2_utils.feature_detect_and_compute(part)
    cv2_utils.show_image(part)

    for c in CHARACTER_LIST:
        template = ih.get_character_avatar_template(c.id)
        r = cv2_utils.feature_match_for_one(
            source_kps, source_desc,
            template.kps, template.desc,
            template.origin.shape[1], template.origin.shape[0]
        )

        if r is not None:
            r.x += 70
            r.y += 160

            print(c.id)
            cv2_utils.show_image(screen, r, wait=0)


if __name__ == '__main__':
    _test_feature_match_for_one()
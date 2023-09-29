import cv2
import numpy as np

from basic.img import cv2_utils


def _test_get_angle_by_pts():
    angle = cv2_utils.get_angle_by_pts((0, 0), (1, 1))
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

if __name__ == '__main__':
    _test_ellipse()
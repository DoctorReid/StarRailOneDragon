import os
import time

import cv2
from cv2.typing import MatLike

from basic import os_utils
from basic.img import cv2_utils


def get_debug_image_dir():
    return os_utils.get_path_under_work_dir('.debug', 'images')


def get_debug_image_path(filename, suffix: str = '.png') -> str:
    return os.path.join(get_debug_image_dir(), filename + suffix)


def get_debug_image(filename, suffix: str = '.png') -> MatLike:
    return cv2_utils.read_image(get_debug_image_path(filename, suffix))


def get_test_image_dir():
    return os_utils.get_path_under_work_dir('test', 'resources', 'images')


def get_test_image_path(filename, suffix: str = '.png') -> str:
    return os.path.join(get_test_image_dir(), filename + suffix)


def get_test_image(filename, suffix: str = '.png') -> MatLike:
    """

    :rtype: object
    """
    return cv2_utils.read_image(get_test_image_path(filename, suffix))


def save_debug_image(image):
    path = get_debug_image_path(str(int(round(time.time() * 1000))))
    print(path)
    print(cv2.imwrite(path, image))
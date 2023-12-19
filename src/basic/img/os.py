import os
import time
from datetime import datetime

import cv2
from cv2.typing import MatLike

from basic import os_utils
from basic.img import cv2_utils
from basic.log_utils import log


def get_debug_image_dir():
    return os_utils.get_path_under_work_dir('.debug', 'images')


def get_debug_world_patrol_dir():
    return os_utils.get_path_under_work_dir('.debug', 'world_patrol')


def get_debug_image_path(filename, suffix: str = '.png') -> str:
    return os.path.join(get_debug_image_dir(), filename + suffix)


def get_debug_image(filename, suffix: str = '.png') -> MatLike:
    return cv2_utils.read_image(get_debug_image_path(filename, suffix))


def get_test_image_dir(sub_dir: str = None):
    if sub_dir is None:
        return os_utils.get_path_under_work_dir('test', 'resources', 'images')
    else:
        return os_utils.get_path_under_work_dir('test', 'resources', 'images', sub_dir)


def get_test_image_path(filename, suffix: str = '.png', sub_dir: str = None) -> str:
    return os.path.join(get_test_image_dir(sub_dir=sub_dir), filename + suffix)


def get_test_image(filename, suffix: str = '.png', sub_dir: str = None) -> MatLike:
    """
    :rtype: object
    """
    return cv2_utils.read_image(get_test_image_path(filename, suffix, sub_dir))


def save_debug_image(image, prefix: str = '') -> str:

    dt_object = datetime.fromtimestamp(time.time())

    formatted_time = dt_object.strftime('%Y-%m-%d_%H-%M-%S')
    file_name = '{}_{}'.format(prefix, formatted_time)
    path = get_debug_image_path(file_name)
    log.debug('临时图片保存 %s', path)
    cv2.imwrite(path, image)
    return file_name

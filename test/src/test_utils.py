import os

from basic import os_utils


def get_debug_image_dir():
    return os_utils.get_path_under_work_dir('.debug', 'images')


def get_debug_image(filename):
    return os.path.join(get_debug_image_dir(), filename)


def get_test_image_dir():
    return os_utils.get_path_under_work_dir('test', 'resources', 'images')


def get_test_image(filename):
    return os.path.join(get_test_image_dir(), filename)

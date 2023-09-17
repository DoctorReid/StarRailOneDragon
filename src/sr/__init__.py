import os

import cv2

from basic import os_utils
from basic.img import cv2_utils


def read_map_image(name) -> cv2.typing.MatLike:
    """
    读取某个地图
    :param name: 地点名称
    :return: 图片
    """
    path = os.path.join(os_utils.get_path_under_work_dir('images', 'map'), '%s.png' % name)
    return cv2_utils.read_image_with_alpha(path)

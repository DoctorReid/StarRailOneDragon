import os

from cv2.typing import MatLike

from basic import os_utils
from basic.img import cv2_utils


def raed_template_image(name) -> MatLike:
    """
    读取某个目标
    :param name: 模板名称
    :return: 图片
    """
    path = os.path.join(os_utils.get_path_under_work_dir('images', 'template'), '%s.png' % name)
    return cv2_utils.read_image(path)
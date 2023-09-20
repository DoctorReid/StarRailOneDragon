import os

import cv2

from basic import os_utils
from basic.img import cv2_utils

def get_map_path(planet: str, region: str, mt: str = 'origin') -> str:
    """
    获取某张地图路径
    :param planet: 星球名称
    :param region: 对应区域
    :param mt: 地图类型
    :return: 图片路径
    """
    return os.path.join(os_utils.get_path_under_work_dir('images', 'map', planet, region), '%s.png' % mt)


def read_map_image(planet: str, region: str, mt: str = 'origin') -> cv2.typing.MatLike:
    """
    读取某个地图
    :param planet: 星球名称
    :param region: 对应区域
    :param mt: 地图类型
    :return: 图片
    """
    path = get_map_path(planet, region, mt)
    return cv2.imread(path, cv2.IMREAD_GRAYSCALE) if mt == 'bw' else cv2_utils.read_image_with_alpha(path)


def save_map_image(image: cv2.typing.MatLike, planet: str, region: str, mt: str = 'origin'):
    """
    保存某张地图
    :param image: 图片
    :param planet: 星球名称
    :param region: 对应区域
    :param mt: 地图类型
    :return:
    """
    path = get_map_path(planet, region, mt)
    cv2.imwrite(path, image)


def raed_template_image(name) -> cv2.typing.MatLike:
    """
    读取某个目标
    :param name: 模板名称
    :return: 图片
    """
    path = os.path.join(os_utils.get_path_under_work_dir('images', 'template'), '%s.png' % name)
    return cv2_utils.read_image_with_alpha(path)
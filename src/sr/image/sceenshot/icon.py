from typing import List

import cv2
import os
import numpy as np
from cv2.typing import MatLike

from basic import os_utils
from basic.img import cv2_utils
from sr.image.image_holder import ImageHolder


def cut_icon_from_black_bg(icon: MatLike, ignore: List = []):
    """
    图标二值化后扣图
    :param icon:
    :param ignore: 额外忽略的部分
    :return:
    """
    # 二值化
    mask = cv2_utils.binary_with_white_alpha(icon)
    # 变成透明
    result = cv2.bitwise_and(icon, icon, mask=mask)
    # 特殊处理
    for i in ignore:
        result = cv2_utils.mark_area_as_transparent(result, i)
    return result


def convert_template(template_id, save: bool = False):
    """
    把抠图后的图标灰度保存
    :param template_id:
    :param save:
    :return:
    """
    ih = ImageHolder()
    template = ih.get_template(template_id)
    gray = cv2.cvtColor(template.origin, cv2.COLOR_BGRA2GRAY)
    mask = np.where(template.origin[..., 3] > 0, 255, 0).astype(np.uint8)
    cv2_utils.show_image(template.origin, win_name='origin')
    cv2_utils.show_image(gray, win_name='gray')
    cv2_utils.show_image(mask, win_name='mask', wait=0)
    if save:
        dir = os_utils.get_path_under_work_dir('images', 'template', template_id)
        cv2.imwrite(os.path.join(dir, 'gray.png'), gray)
        cv2.imwrite(os.path.join(dir, 'mask.png'), mask)


def init_icon_with_background(template_id: str):
    """
    将裁剪出来的图片 转化保留灰度图和对应掩码
    :param template_id:
    :return:
    """
    ih = ImageHolder()
    template = ih.get_template(template_id)
    gray = cv2.cvtColor(template.origin, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, np.mean(gray), 255, cv2.THRESH_BINARY)
    mask = cv2_utils.connection_erase(binary, threshold=5)
    cv2_utils.show_image(template.origin, win_name='origin')
    cv2_utils.show_image(gray, win_name='gray')
    cv2_utils.show_image(mask, win_name='mask')

    cv2.waitKey(0)

    save_template_image(gray, template_id, 'gray')
    save_template_image(mask, template_id, 'mask')


def save_template_image(img: MatLike, template_id: str, tt: str):
    """
    保存模板图片
    :param img: 模板图片
    :param template_id: 模板id
    :param tt: 模板类型
    :return:
    """
    path = os_utils.get_path_under_work_dir('images', 'template', template_id)
    print(path)
    print(cv2.imwrite(os.path.join(path, '%s.png' % tt), img))

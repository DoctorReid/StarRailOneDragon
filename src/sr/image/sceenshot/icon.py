from typing import List

import cv2
import os
import numpy as np
from cv2.typing import MatLike

from basic import os_utils
from basic.img import cv2_utils
from sr import constants
from sr.image.image_holder import ImageHolder


def _read_template_image(template_id):
    dir_path = os.path.join(os_utils.get_path_under_work_dir('images', 'template'), template_id)
    if not os.path.exists(dir_path):
        return None
    img = cv2_utils.read_image(os.path.join(dir_path, 'raw.png'))

    if img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    return img

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


def init_tp_with_background(template_id: str):
    """
    对传送点进行抠图
    将裁剪出来的图片 转化保留灰度图和对应掩码
    如果原图有透明通道 会转化成无透明通道的
    最后结果图都会转化到 50*50 并居中
    会覆盖原图 发现有问题可在图片显示时退出程序
    :param template_id:
    :return:
    """
    origin = _read_template_image(template_id)
    gray = cv2.cvtColor(origin, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, np.mean(gray), 255, cv2.THRESH_BINARY)
    mask = cv2_utils.connection_erase(binary, threshold=30)

    # 背景统一使用道路颜色 因为地图上传送点附近大概率都是道路 这样更方便匹配
    final_origin, final_gray, final_mask = convert_to_standard(origin, mask, constants.COLOR_MAP_ROAD_BGR)

    cv2_utils.show_image(final_origin, win_name='origin')
    cv2_utils.show_image(final_gray, win_name='gray')
    cv2_utils.show_image(final_mask, win_name='mask')

    cv2.waitKey(0)

    save_template_image(final_origin, template_id, 'origin')
    save_template_image(final_gray, template_id, 'gray')
    save_template_image(final_mask, template_id, 'mask')

def init_sp_with_background(template_id: str, noise_threshold: int = 0):
    """
    对特殊点进行抠图
    特殊点会自带一些黑色背景 通过找黑色的菱形区域保留下来
    将裁剪出来的图片 转化保留灰度图和对应掩码
    如果原图有透明通道 会转化成无透明通道的
    最后结果图都会转化到 50*50 并居中
    会覆盖原图 发现有问题可在图片显示时退出程序
    :param template_id:
    :param noise_threshold: 连通块小于多少时认为是噪点 视情况调整
    :return:
    """
    raw = _read_template_image(template_id)
    sim = cv2_utils.color_similarity_2d(raw, (160, 210, 240))  # 前景颜色 特殊点主体部分
    cv2_utils.show_image(sim, win_name='sim')
    front_binary = cv2.inRange(sim, 180, 255)
    cv2_utils.show_image(front_binary, win_name='front_binary')

    # 画出黑色的菱形背景
    gray = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
    cv2_utils.show_image(gray, win_name='gray')
    black = cv2.inRange(gray, 0, 20)

    l1, r1, t1, b1 = get_four_conner(black)
    print(l1, r1, t1, b1)
    # 找特殊点主体部分的几个角 可能会覆盖到菱形
    l2, r2, t2, b2 = get_four_conner(front_binary)
    print(l2, r2, t2, b2)
    l = l1 if l1[0] < l2[0] else l2
    r = r1 if r1[0] > r2[0] else r2
    t = t1 if t1[1] < t2[1] else t2
    b = b1 if b1[1] > b2[1] else b2

    points = np.array([l, t, r, b], np.int32)
    points = points.reshape((-1, 1, 2))
    back_binary = np.zeros_like(gray)
    cv2.fillPoly(back_binary, [points], color=255)
    cv2_utils.show_image(back_binary, win_name='back_binary')

    binary = cv2.bitwise_or(front_binary, back_binary)
    cv2_utils.show_image(binary, win_name='binary')
    mask = cv2_utils.connection_erase(binary, threshold=noise_threshold)
    mask = cv2_utils.connection_erase(mask, threshold=noise_threshold, erase_white=False)

    final_origin, final_gray, final_mask = convert_to_standard(raw, mask, constants.COLOR_MAP_ROAD_BGR)

    cv2_utils.show_image(final_origin, win_name='origin')
    cv2_utils.show_image(final_gray, win_name='gray')
    cv2_utils.show_image(final_mask, win_name='mask')

    cv2.waitKey(0)

    save_template_image(final_origin, template_id, 'origin')
    save_template_image(final_gray, template_id, 'gray')
    save_template_image(final_mask, template_id, 'mask')

def get_four_conner(bw):
    """
    获取四个方向最远的白色像素点的位置
    :param bw: 黑白图
    :return:
    """
    white = np.where(bw == 255)
    left = (white[1][np.argmin(white[1])], white[0][np.argmin(white[1])])
    right = (white[1][np.argmax(white[1])], white[0][np.argmax(white[1])])
    top = (white[1][np.argmin(white[0])], white[0][np.argmin(white[0])])
    bottom = (white[1][np.argmax(white[0])], white[0][np.argmax(white[0])])
    return left, right, top, bottom
    

def convert_to_standard(origin, mask, bg_color = None):
    """
    转化成 50*50 并居中
    :param origin:
    :param mask:
    :param bg_color: 背景色
    :return:
    """
    bw = np.where(mask == 255)
    white_pixel_coordinates = list(zip(bw[1], bw[0]))

    # 找到最大最小坐标值
    max_x = max(white_pixel_coordinates, key=lambda c: c[0])[0]
    max_y = max(white_pixel_coordinates, key=lambda c: c[1])[1]

    min_x = min(white_pixel_coordinates, key=lambda c: c[0])[0]
    min_y = min(white_pixel_coordinates, key=lambda c: c[1])[1]
    print(min_x, min_y, max_x, max_y)

    # 稍微扩大一下范围
    if max_x < mask.shape[1]:
        max_x += min(5, mask.shape[1] - max_x)
    if max_y < mask.shape[0]:
        max_y += min(5, mask.shape[0] - max_y)
    if min_x > 0:
        min_x -= min(5, min_x)
    if min_y > 0:
        min_y -= min(5, min_y)

    cx = (min_x + max_x) // 2
    cy = (min_y + max_y) // 2

    x1, y1 = cx - min_x, cy - min_y
    x2, y2 = max_x - cx, max_y - cy

    # 移动到 50*50 居中
    final_mask = np.zeros((50, 50), dtype=np.uint8)
    final_mask[25-y1:25+y2, 25-x1:25+x2] = mask[min_y:max_y, min_x:max_x]

    final_origin = np.zeros((50, 50, 3), dtype=np.uint8)
    final_origin[25-y1:25+y2, 25-x1:25+x2, :] = origin[min_y:max_y, min_x:max_x, :]
    final_origin = cv2.bitwise_and(final_origin, final_origin, mask=final_mask)

    if bg_color is not None:  # 部分图标可以背景统一使用颜色
        final_origin[np.where(final_mask == 0)] = bg_color

    final_gray = cv2.cvtColor(final_origin, cv2.COLOR_BGR2GRAY)

    return final_origin, final_gray, final_mask


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

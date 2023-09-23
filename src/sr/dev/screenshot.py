import os
import time
from typing import List

import cv2
import numpy as np
import pyautogui

import sr
from basic import gui_utils, os_utils
from basic.img import cv2_utils
from sr import constants, dev
from sr.config import ConfigHolder
from sr.image.cv2_matcher import CvImageMatcher
from sr.image.image_holder import ImageHolder
from sr.map_cal import MapCalculator


def screenshot_game(no_uid: bool = True, save_result: bool = True, show_result: bool = False):
    """
    对游戏窗口进行截图
    :param no_uid: 是否屏幕uid部分
    :param save_result: 是否显示结果
    :param show_result: 是否显示截图
    :return:
    """
    win = gui_utils.get_win_by_name('崩坏：星穹铁道', active=True)
    # 移开鼠标
    pyautogui.moveTo(1, 1)
    img = gui_utils.screenshot_win(win)
    if no_uid:
        cv2_utils.mark_area_as_color(img, [0, 1080, 200, 100], constants.COLOR_MAP_ROAD_BGR)
    if show_result:
        cv2_utils.show_image(img)
    if save_result:
        dev.save_debug_image(img)
    return img


def screenshot_map_vertically(save_each: bool = False, save_merge: bool = True, show_merge: bool = False):
    """
    使用垂直滚动的方式对大地图进行截图，并进行垂直方向的拼接。
    结果图使用美图秀秀自动扣图和裁剪即可。
    :param save_each: 是否保存中间截图结果
    :param save_merge: 是否保存最终拼接结果
    :param show_merge: 是否显示最终拼接结果
    :return: 完整的大地图
    """
    win = gui_utils.get_win_by_name('崩坏：星穹铁道', active=True)
    # 先拉取到最上方
    gui_utils.scroll_with_mouse_press([win.topleft.x + 1300, win.topleft.y + 500], down_distance=-1000, duration=1)
    time.sleep(1)
    img = []
    # 每秒往下滚动一次截图
    for i in range(10):
        no_uid = screenshot_game(no_uid=False, save_result=False)
        map_part = no_uid[250: 900, 200: 1400]
        if len(img) == 0 or not cv2_utils.is_same_image(img[len(img) - 1], map_part):
            img.append(map_part)
            if save_each:
                dev.save_debug_image(map_part)
            gui_utils.scroll_with_mouse_press([win.topleft.x + 1300, win.topleft.y + 500], down_distance=300)
            time.sleep(1)
        else:
            break

    merge = img[0]
    for i in range(len(img)):
        if i == 0:
            merge = img[i]
        else:
            merge = cv2_utils.concat_vertically(merge, img[i])

    if show_merge:
        cv2_utils.show_image(merge)

    if save_merge:
        dev.save_debug_image(merge)


def cut_icon_from_black_bg(icon: cv2.typing.MatLike, special_parts: List = []):
    """
    图标二值化后扣图
    :param icon:
    :param special_parts:
    :return:
    """
    # 二值化
    mask = cv2_utils.binary_with_white_alpha(icon)
    # 变成透明
    result = cv2.bitwise_and(icon, icon, mask=mask)
    # 特殊处理
    for i in special_parts:
        result = cv2_utils.mark_area_as_transparent(result, i)
    return result


def convert_debug_transport(name: str, special_parts: List = [], save: bool = True):
    t = dev.get_debug_image(name)
    t2 = cut_icon_from_black_bg(t, special_parts=special_parts)
    if save:
        dev.save_debug_image(t2)
    cv2_utils.show_image(t2, wait=0)


def convert_origin_map(planet: str, region: str, save: bool = True) -> cv2.typing.MatLike:
    """
    将大地图转化成黑白图，黑色为可以走的部分
    再将使用黑白图从原图中扣出细化的地图，用作后续匹配
    :param planet: 星球名称
    :param region: 对应区域
    :param save: 是否保存
    :return:
    """
    ih = ImageHolder()
    im = CvImageMatcher()
    ch = ConfigHolder()
    mc = MapCalculator(im=im, config=ch)
    large_map = ih.get_large_map(planet, region, 'origin')
    lm = mc.analyse_large_map(large_map)
    cv2_utils.show_image(lm.gray, win_name='gray')
    cv2_utils.show_image(lm.mask, win_name='mask')
    if save:
        sr.save_map_image(lm.gray, planet, region, 'gray')
        sr.save_map_image(lm.mask, planet, region, 'mask')
    cv2.waitKey(0)


def convert_arrow_color(arrow: cv2.typing.MatLike, save: bool = True):
    alpha = arrow[:, :, 3]
    alpha[np.where(alpha > 0)] = 255

    arrow[:, :, 3] = alpha

    # 按箭头颜色圈出
    lower_color = np.array([210, 190, 0, 255])
    upper_color = np.array([255, 240, 60, 255])
    road_mask = cv2.inRange(arrow, lower_color, upper_color)

    cv2_utils.show_image(road_mask, win_name='road_mask')
    # 找到连通块 过滤旁边的噪点
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(road_mask, connectivity=8)
    large_components = []
    for label in range(1, num_labels):
        if stats[label, cv2.CC_STAT_AREA] > 100:
            large_components.append(label)

    # 创建一个新的 只保留连通部分
    mask = np.zeros(alpha.shape[:2], dtype=np.uint8)
    for label in large_components:
        mask[labels == label] = 255

    new_arrow = np.zeros_like(arrow)
    new_arrow[np.where(mask > 0)] = constants.COLOR_ARROW_BGRA
    cv2_utils.show_image(new_arrow, win_name='new_arrow')
    cv2.waitKey(0)
    if save:
        dev.save_debug_image(new_arrow)


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


if __name__ == '__main__':
    # convert_origin_map(constants.PLANET_1_KZJ, constants.REGION_2_JZCD, save=True)
    convert_template('exit_1', save=True)
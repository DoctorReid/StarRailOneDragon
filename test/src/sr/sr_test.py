import math
import time
import os

import cv2
import numpy as np
import pyautogui

import dev
import sr
from basic import gui_utils
from basic.img import cv2_utils
from sr.image import ImageMatcher
from sr.image.cv2_matcher import CvImageMatcher
from dev import screenshot
from sr import constants
from sr.config import ConfigHolder
from sr.image.image_holder import ImageHolder
from sr.map_cal import MapCalculator

image_holder = ImageHolder()
im = CvImageMatcher()
ch = ConfigHolder()
mc = MapCalculator(im=im, config=ch)


def _test_standard_little_map(show: bool = False):
    """
    用标准图更新小地图位置
    :param show:
    :return:
    """
    screen = dev.get_test_image('game1')
    mc.cal_little_map_pos(screen)
    print(mc.map_pos)
    little_map = mc.cut_little_map(screen)
    if show:
        cv2_utils.show_image(little_map)
    ch.update_config('game', 'little_map', {'x': mc.map_pos.x, 'y': mc.map_pos.y, 'r': mc.map_pos.r})


def _test_cut_little_map(running: bool = False, save: bool = False):
    if running:
        win = gui_utils.get_win_by_name('崩坏：星穹铁道', active=True)
        gui_utils.screenshot_win(win)
        pyautogui.keyDown('w')
        time.sleep(2)  # 暂停一会 让角色跑起来
    image = screenshot.screenshot_game(no_uid=False, save_result=False, show_result=False)
    mc.cal_little_map_pos(image)
    print(mc.map_pos)
    little_map = mc.cut_little_map(image)
    cv2_utils.show_image(little_map)
    if save:
        dev.save_debug_image(little_map)


def _test_little_map_arrow():
    screen = dev.get_test_image('game4')
    little_map = mc.cut_little_map(screen)
    arrow = mc.cut_little_map_arrow(little_map)
    cv2_utils.show_image(arrow, win_name='arrow')
    cv2_utils.show_image(cv2_utils.image_rotate(arrow, 90), win_name='arrow-2')
    cv2_utils.show_image(cv2_utils.image_rotate(arrow, 180), win_name='arrow-3')
    cv2_utils.show_image(cv2_utils.image_rotate(arrow, 270), win_name='arrow-4')
    print(mc.get_angle_from_arrow_image(arrow))
    cv2.waitKey(0)


def _test_little_map_radio_mask():
    for i in range(4):
        screen = dev.get_test_image('game%d' % (i+1))
        little_map = mc.cut_little_map(screen)
        cv2_utils.show_image(little_map, win_name='little_map')
        angle = mc.get_cv_angle_from_little_map(little_map)
        mask = mc.find_little_map_radio_mask(little_map, angle)
        cv2_utils.show_image(mask, win_name='mask', wait=0)


def _test_find_map_road_mask():
    screen = dev.get_test_image('game3')
    little_map = mc.cut_little_map(screen)
    cv2_utils.show_image(little_map, win_name='little_map')
    arrow_mask = mc.find_little_map_arrow_mask(little_map)
    cv2_utils.show_image(arrow_mask, win_name='arrow_mask')
    cv2_utils.show_image(mc.find_map_road_mask(little_map, is_little_map=True), win_name='mask', wait=0)


def _test_find_map_special_point_mask():
    screen = dev.get_test_image('game3')
    little_map = mc.cut_little_map(screen)
    cv2_utils.show_image(little_map, win_name='little_map')
    mask, _ = mc.find_map_special_point_mask(little_map, is_little_map=True)
    cv2_utils.show_image(mask, win_name='mask', wait=0)


def _test_find_map_arrow_mask():
    screen = dev.get_test_image('game2')
    little_map = mc.cut_little_map(screen)
    cv2_utils.show_image(little_map, win_name='little_map')
    mask = mc.find_little_map_arrow_mask(little_map)
    cv2_utils.show_image(mask, win_name='mask')
    # 黑色边缘线条采集不到 稍微膨胀一下
    kernel = np.ones((7, 7), np.uint8)
    expand_arrow_mask = cv2.dilate(mask, kernel, iterations=1)
    cv2_utils.show_image(expand_arrow_mask, win_name='expand_arrow_mask', wait=0)


def _test_little_map_road_edge_mask():
    for i in range(4):
        screen = dev.get_test_image('game%d' % (i+1))
        little_map = mc.cut_little_map(screen)
        mask = mc.find_little_map_edge_mask(little_map, None)
        cv2_utils.show_image(mask, win_name='mask')
        little_map[np.where(mask>0)] = [255,0,0,255]
        cv2_utils.show_image(little_map, win_name='little_map', wait=0)


def _test_auto_cut_map():
    for i in range(5):
        screen = dev.get_test_image('game%d' % (i+1))
        little_map = mc.cut_little_map(screen)
        cv2_utils.show_image(little_map, win_name='little_map')
        usage, bw, _ = mc.auto_cut_map(little_map, is_little_map=True, show=True)
        cv2.waitKey(0)


def _test_cal_character_pos_by_match():
    large_map_usage = image_holder.get_large_map(constants.PLANET_1_KZJ, constants.REGION_2_JZCD, 'gray')
    large_map_mask = image_holder.get_large_map(constants.PLANET_1_KZJ, constants.REGION_2_JZCD, 'mask')
    for i in range(5):
        screen = dev.get_test_image('game%d' % (i+1))
        little_map = mc.cut_little_map(screen)
        little_map_usage, little_map_mask, little_map_sp = mc.auto_cut_map(little_map, is_little_map=True)
        # mc.cal_character_pos_by_match(little_map, large_map_usage, show=True)
        # cv2.waitKey(0)
        x, y = mc.cal_character_pos_by_feature(large_map_usage, large_map_mask,
                                               little_map_usage, little_map_mask, little_map_sp,
                                               possible_pos=(280, 100, 0),
                                               show=True)
        print(x,y)
        cv2.waitKey(0)


def _test_cal_character_pos_by_match_2():
    large_map_usage = image_holder.get_large_map(constants.PLANET_1_KZJ, constants.REGION_2_JZCD, 'gray')
    large_map_mask = image_holder.get_large_map(constants.PLANET_1_KZJ, constants.REGION_2_JZCD, 'mask')

    dir = dev.get_debug_image_dir()
    for filename in os.listdir(dir):
        # if filename != '1695048928114.png':
        #     continue
        print(filename)
        screen = cv2_utils.read_image(os.path.join(dir, filename))
        little_map = mc.cut_little_map(screen)
        little_map_usage, little_map_mask, little_map_sp = mc.auto_cut_map(little_map, is_little_map=True, show=True)
        x, y = mc.cal_character_pos_by_feature(large_map_usage, large_map_mask,
                                               little_map_usage, little_map_mask, little_map_sp,
                                               possible_pos=(280, 100, 0),
                                               show=True)
        print(x,y)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    pass

if __name__ == '__main__':
    _test_cal_character_pos_by_match_2()
    cv2.waitKey(0)
    # win = gui_utils.get_win_by_name('崩坏：星穹铁道', active=True)
    # time.sleep(1)
    # calibrator = Calibrator(win, ch, mc)
    # calibrator._check_move_distance(save_screenshot=True)

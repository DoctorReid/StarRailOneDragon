import time

import cv2
import numpy as np
import pyautogui

import dev
import sr
from basic import gui_utils
from basic.img import cv2_utils, ImageMatcher
from basic.img.cv2_matcher import CvImageMatcher
from dev import screenshot
from sr import constants
from sr.calibrator import Calibrator
from sr.config import ConfigHolder
from sr.map_cal import MapCalculator

im = CvImageMatcher()
ch = ConfigHolder()
mc = MapCalculator(im=im, config=ch)


def _test_standard_little_map(show: bool = False):
    """
    用标准图更新小地图位置
    :param show:
    :return:
    """
    screen = cv2_utils.read_image_with_alpha(dev.get_test_image('game1.png'))
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
    image = cv2_utils.read_image_with_alpha(dev.get_test_image('game1.png'))
    arrow_1 = mc.cut_little_map_arrow(image)
    cv2_utils.show_image(arrow_1)
    mc.cal_little_map_pos(image)
    arrow_2 = mc.cut_little_map_arrow(image)
    cv2_utils.show_image(arrow_2)


def _test_get_direction_by_screenshot():
    matcher: ImageMatcher = CvImageMatcher()
    matcher.load_template('loc_arrow', dev.get_test_image('loc_arrow.png'))
    game = cv2_utils.read_image_with_alpha(dev.get_test_image('game1.png'))
    mc.cal_little_map_pos(game)
    print(mc.get_direction_by_screenshot(game, matcher, show_match_result=True))


def _test_find_map_road_mask():
    screen = dev.get_test_image('game3')
    little_map = mc.cut_little_map(screen)
    cv2_utils.show_image(little_map, win_name='little_map', wait=0)
    cv2_utils.show_image(mc.find_map_road_mask(little_map), win_name='mask', wait=0)


def _test_find_map_special_point_mask():
    screen = dev.get_test_image('game3')
    little_map = mc.cut_little_map(screen)
    cv2_utils.show_image(little_map, win_name='little_map')
    mask, _ = mc.find_map_special_point_mask(little_map, is_little_map=True)
    cv2_utils.show_image(mask, win_name='mask', wait=0)


def _test_find_map_arrow_mask():
    screen = dev.get_test_image('game3')
    little_map = mc.cut_little_map(screen)
    cv2_utils.show_image(little_map, win_name='little_map', wait=0)
    cv2_utils.show_image(mc.find_map_arrow_mask(little_map), win_name='mask', wait=0)


def _test_auto_cut_map():
    screen = dev.get_test_image('game3')
    little_map = mc.cut_little_map(screen)
    cv2_utils.show_image(little_map, win_name='little_map')
    bw, usage, _ = mc.auto_cut_map(little_map, is_little_map=True, show=True)
    cv2.waitKey(0)


def _test_cal_character_pos_by_match():
    """
    使用黑白图和灰度图进行小地图匹配的 效果不太行 代码先留着
    :return:
    """
    large_map = sr.read_map_image(constants.PLANET_1_KZJ, constants.REGION_2_JZCD, 'usage')
    for i in range(4):
        screen = dev.get_test_image('game%d' % (i+1))
        little_map = mc.cut_little_map(screen)
        mc.cal_character_pos_by_match(little_map, large_map, show=True)
        cv2.waitKey(0)
        # mc.cal_character_pos_by_feature(little_map, large_map, show=True)
        # cv2.waitKey(0)


def _test_match_little_map2():
    lm = cv2_utils.read_image_with_alpha(dev.get_test_image('game2.png'))
    m = sr.read_map_image(constants.PLANET_1_KZJ, constants.REGION_2_JZCD, 'bw')
    print(mc.cal_character_pos(lm, m, show=True))
    cv2.waitKey(0)


if __name__ == '__main__':
    # _test_cal_character_pos_by_match()
    win = gui_utils.get_win_by_name('崩坏：星穹铁道', active=True)
    time.sleep(1)
    calibrator = Calibrator(win, ch, mc)
    calibrator._check_move_distance(save_screenshot=True)

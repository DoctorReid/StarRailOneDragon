import os
import time

import cv2
import numpy as np

from basic.img import cv2_utils
from basic.img.os import get_test_image, get_debug_image_dir
from sr import constants
from sr.config import ConfigHolder
from sr.image.cv2_matcher import CvImageMatcher
from sr.image.image_holder import ImageHolder
from sr.map_cal import MapCalculator

image_holder = ImageHolder()
im = CvImageMatcher()
ch = ConfigHolder()
mc = MapCalculator(im=im, config=ch)


def _test_analyse_mini_map():
    dir = get_debug_image_dir()
    for filename in os.listdir(dir):
        screen = cv2_utils.read_image(os.path.join(dir, filename))
        # if filename != '1695658278789.png':
        #     continue
        print(filename)
        mm = mc.cut_mini_map(screen)
        info = mc.analyse_mini_map(mm)
        print('角度', info.angle)
        cv2_utils.show_image(info.sp_mask, win_name='sp_mask')
        cv2_utils.show_image(info.center_arrow_mask, win_name='center_arrow_mask')
        cv2_utils.show_image(info.road_mask, win_name='road_mask')
        cv2_utils.show_image(info.edge, win_name='edge')
        cv2_utils.show_image(info.feature_mask, win_name='feature_mask')
        cv2.waitKey(0)
        cv2.destroyAllWindows()


def _test_little_map_radio_mask():
    for i in range(4):
        screen = get_test_image('game%d' % (i + 1))
        little_map = mc.cut_mini_map(screen)
        cv2_utils.show_image(little_map, win_name='little_map')
        angle = mc.get_cv_angle_from_little_map(little_map)
        mask = mc.find_little_map_radio_mask(little_map, angle)
        cv2_utils.show_image(mask, win_name='mask', wait=0)


def _test_find_map_road_mask():
    screen = get_test_image('game3')
    little_map = mc.cut_mini_map(screen)
    cv2_utils.show_image(little_map, win_name='little_map')
    arrow_mask = mc.find_little_map_arrow_mask(little_map)
    cv2_utils.show_image(arrow_mask, win_name='arrow_mask')
    cv2_utils.show_image(mc.find_map_road_mask(little_map, is_little_map=True), win_name='mask', wait=0)


def _test_find_map_special_point_mask():
    screen = get_test_image('game3')
    little_map = mc.cut_mini_map(screen)
    cv2_utils.show_image(little_map, win_name='little_map')
    st = time.time()
    mask, _ = mc.find_map_special_point_mask(little_map, is_little_map=True)
    print('%.5f' % (time.time() - st))
    cv2_utils.show_image(mask, win_name='mask', wait=0)


def _test_find_map_arrow_mask():
    screen = get_test_image('game2')
    little_map = mc.cut_mini_map(screen)
    cv2_utils.show_image(little_map, win_name='little_map')
    mask = mc.find_little_map_arrow_mask(little_map)
    cv2_utils.show_image(mask, win_name='mask')
    # 黑色边缘线条采集不到 稍微膨胀一下
    kernel = np.ones((7, 7), np.uint8)
    expand_arrow_mask = cv2.dilate(mask, kernel, iterations=1)
    cv2_utils.show_image(expand_arrow_mask, win_name='expand_arrow_mask', wait=0)


def _test_little_map_road_edge_mask():
    for i in range(4):
        screen = get_test_image('game%d' % (i + 1))
        little_map = mc.cut_mini_map(screen)
        mask = mc.find_little_map_edge_mask(little_map, None)
        cv2_utils.show_image(mask, win_name='mask')
        little_map[np.where(mask>0)] = [255,0,0,255]
        cv2_utils.show_image(little_map, win_name='little_map', wait=0)


def _test_cal_character_pos_by_match():
    lm = image_holder.get_large_map(constants.PLANET_1_KZJ, constants.REGION_2_JZCD, 'origin')
    lm_info = mc.analyse_large_map(lm)

    dir = get_debug_image_dir()
    for filename in os.listdir(dir):
        screen = cv2_utils.read_image(os.path.join(dir, filename))
        # if filename != '1695046757045.png':
        #     continue
        print(filename)

    # for i in range(5):
    #     if i < 4:
    #         continue
    #     screen = dev.get_test_image('game%d' % (i+1))
        mm = mc.cut_mini_map(screen)
        mm_info = mc.analyse_mini_map(mm)
        cv2_utils.show_image(mm_info.gray, win_name='mini_map_gray')
        cv2_utils.show_image(mm_info.feature_mask, win_name='feature_mask')
        x, y = mc.cal_character_pos_with_scale(lm_info, mm_info,
                                               possible_pos=(285, 140, 20),
                                               show=True)
        print(x,y)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == '__main__':
    _test_analyse_mini_map()
    # win = gui_utils.get_win_by_name('崩坏：星穹铁道', active=True)
    # time.sleep(1)
    # calibrator = Calibrator(win, ch, mc)
    # calibrator._check_move_distance(save_screenshot=True)
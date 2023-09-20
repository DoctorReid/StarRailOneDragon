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
    screen = dev.get_test_image('game2')
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
        # mc.cal_character_pos_by_match(little_map, large_map, show=True)
        # cv2.waitKey(0)
        mc.cal_character_pos_by_feature(little_map, large_map, show=True)
        cv2.waitKey(0)


def _test_cal_character_pos_by_match_2():
    large_map = sr.read_map_image(constants.PLANET_1_KZJ, constants.REGION_2_JZCD, 'origin')
    large_map_bw, large_map_usage, _ = mc.auto_cut_map(large_map, is_little_map=False)
    screen = dev.get_test_image('game2')
    little_map = mc.cut_little_map(screen)
    little_map_bw, little_map_usage, _ = mc.auto_cut_map(little_map, is_little_map=True)

    source = cv2.cvtColor(large_map_usage, cv2.COLOR_BGRA2GRAY)
    template = cv2.cvtColor(little_map_usage, cv2.COLOR_BGRA2GRAY)
    cv2_utils.show_image(source, win_name='source')
    cv2_utils.show_image(template, win_name='template')

    # 创建ORB对象
    orb = cv2.SIFT_create()

    # 在模板图像和原图中提取特征点和描述子
    kp1, des1 = orb.detectAndCompute(source, mask=large_map_bw)
    kp2, des2 = orb.detectAndCompute(template, mask=little_map_bw)
    # 转换描述子数据类型为CV_32F
    des1 = np.float32(des1)
    des2 = np.float32(des2)

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.knnMatch(des1, des2, k=2)
    all_result = cv2.drawMatches(source, kp1, template, kp2, matches, None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
    cv2_utils.show_image(all_result, win_name='all_match')

    # 筛选匹配点
    matches = sorted(matches, key=lambda x: x.distance)

    # 提取匹配点的坐标
    src_pts = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)

    # 使用RANSAC算法估计模板的位置和姿态
    M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

    # 获取模板的宽度和高度
    h, w = template.shape

    # 定义模板的四个角点
    corners = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)

    # 将模板的四个角点变换到原图中的位置
    dst_corners = cv2.perspectiveTransform(corners, M)

    # 绘制模板在原图中的位置
    original_with_template = cv2.polylines(source, [np.int32(dst_corners)], True, 255, 3, cv2.LINE_AA)

    # 显示结果
    cv2.imshow('Template in Original', original_with_template)
    # cv2_utils.show_image(little_map, win_name='little_map')
    # bw, usage, _ = mc.auto_cut_map(little_map, is_little_map=True, show=True)
    # mc.cal_character_pos_by_match(little_map, large_map, show=True)
    # mc.cal_character_pos_by_feature(little_map, large_map, show=True)
    cv2.waitKey(0)


if __name__ == '__main__':
    _test_cal_character_pos_by_match_2()
    # win = gui_utils.get_win_by_name('崩坏：星穹铁道', active=True)
    # time.sleep(1)
    # calibrator = Calibrator(win, ch, mc)
    # calibrator._check_move_distance(save_screenshot=True)

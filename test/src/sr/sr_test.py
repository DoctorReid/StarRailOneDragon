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
    for i in range(4):
        screen = dev.get_test_image('game%d' % (i+1))
        little_map = mc.cut_little_map(screen)
        cv2_utils.show_image(little_map, win_name='little_map')
        usage, bw, _ = mc.auto_cut_map(little_map, is_little_map=True, show=True)
        cv2.waitKey(0)


def _test_cal_character_pos_by_match():
    large_map_usage = image_holder.get_large_map(constants.PLANET_1_KZJ, constants.REGION_2_JZCD, 'gray')
    large_map_mask = image_holder.get_large_map(constants.PLANET_1_KZJ, constants.REGION_2_JZCD, 'mask')
    for i in range(4):
        screen = dev.get_test_image('game%d' % (i+1))
        little_map = mc.cut_little_map(screen)
        little_map_usage, little_map_mask, _ = mc.auto_cut_map(little_map, is_little_map=True)
        # mc.cal_character_pos_by_match(little_map, large_map_usage, show=True)
        # cv2.waitKey(0)
        x, y = mc.cal_character_pos_by_feature(little_map_usage, large_map_usage,
                                               little_map_mask, large_map_mask,
                                               possible_pos=(280, 80, 0),
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
        little_map_usage, little_map_mask, _ = mc.auto_cut_map(little_map, is_little_map=True, show=True)
        # mc.cal_character_pos_by_match(little_map, large_map_usage, show=True)
        # cv2.waitKey(0)
        x, y = mc.cal_character_pos(little_map_usage, large_map_usage,
                                               little_map_mask, large_map_mask,
                                    possible_pos=(284, 80, 0),
                                               show=True)
        print(x,y)
        cv2.waitKey(0)
    pass

def _test_cal_character_pos_by_match_3():
    """
    使用道路边缘做匹配 效果不太好 先保留代码
    :return:
    """
    large_map_origin = image_holder.get_large_map(constants.PLANET_1_KZJ, constants.REGION_2_JZCD, 'origin')
    large_map_usage, large_map_bw, _ = mc.auto_cut_map(large_map_origin)
    large_map_edge_mask = mc.find_large_map_edge_mask(large_map_bw)
    show = True
    for i in range(4):
        screen = dev.get_test_image('game%d' % (i+1))
        little_map = mc.cut_little_map(screen)
        little_map_usage, little_map_bw, _ = mc.auto_cut_map(little_map, is_little_map=True)
        little_map_edge_mask = mc.find_large_map_edge_mask(little_map_bw)
        cv2_utils.show_image(large_map_edge_mask, win_name='large_map_edge_mask')
        cv2_utils.show_image(little_map_edge_mask, win_name='little_map_edge_mask')

        source = large_map_usage
        source_mask = large_map_usage
        template = little_map_usage
        template_mask = np.zeros_like(template)

        template_h, template_w = template.shape[1], template.shape[0]  # 小地图要只判断中间正方形 圆形边缘会扭曲原来特征
        template_cx, template_cy = template_w // 2, template_h // 2
        template_r = math.floor(template_h / math.sqrt(2) / 2)
        template_mask[template_cy - template_r:template_cy + template_r, template_cx - template_r:template_cx + template_r] = \
            little_map_bw[template_cy - template_r:template_cy + template_r, template_cx - template_r:template_cx + template_r]

        # 在模板和原图中提取特征点和描述子
        sift = cv2.SIFT_create()
        kp1, des1 = sift.detectAndCompute(little_map_edge_mask, mask=template_mask)
        kp2, des2 = sift.detectAndCompute(large_map_edge_mask, mask=None)

        bf = cv2.BFMatcher()
        matches = bf.knnMatch(des1, des2, k=2)
        # 应用比值测试，筛选匹配点
        good_matches = []
        for m, n in matches:
            if m.distance < 0.75 * n.distance:
                good_matches.append(m)

        if show:
            all_result = cv2.drawMatches(template, kp1, source, kp2, good_matches, None, flags=2)
            cv2_utils.show_image(all_result, win_name='all_match')

        if len(good_matches) < 4:  # 不足4个优秀匹配点时 不能使用RANSAC
            return -1, -1

        # 提取匹配点的坐标
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)  # 模板的
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)  # 原图的

        # 使用RANSAC算法估计模板位置和尺度
        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0, mask=source_mask)
        # 获取内点的索引 拿最高置信度的
        inlier_indices = np.where(mask.ravel() == 1)[0]
        if len(inlier_indices) == 0:  # mask 里没找到就算了 再用good_matches的结果也是很不准的
            return -1, -1

        # 距离最短 置信度最高的结果
        best_match = None
        for i in range(len(good_matches)):
            if mask[i] == 1 and (best_match is None or good_matches[i].distance < best_match.distance):
                best_match = good_matches[i]

        template_h, template_w = template.shape[1], template.shape[0]

        query_point = kp2[best_match.trainIdx].pt  # 原图中的关键点坐标 (x, y)
        train_point = kp1[best_match.queryIdx].pt  # 模板中的关键点坐标 (x, y)

        # 获取最佳匹配的特征点的缩放比例 小地图在人物跑动时会缩放
        query_scale = kp2[best_match.trainIdx].size
        train_scale = kp1[best_match.queryIdx].size
        scale = query_scale / train_scale

        # 小地图缩放后偏移量
        offset_x = query_point[0] - train_point[0] * scale
        offset_y = query_point[1] - train_point[1] * scale

        # 小地图缩放后的宽度和高度
        scaled_width = int(template_w * scale)
        scaled_height = int(template_h * scale)

        # 大地图可能剪裁过 加上剪裁的offset
        offset_x = offset_x
        offset_y = offset_y

        # 小地图缩放后中心点在大地图的位置 即人物坐标
        center_x = offset_x + scaled_width // 2
        center_y = offset_y + scaled_height // 2

        if show:
            cv2_utils.show_overlap(large_map_usage, little_map_usage, offset_x, offset_y, template_scale=scale, win_name='overlap')
            if M is not None:
                to_draw_rect = source.copy()
                corners = np.float32([[0, 0], [0, template_h - 1], [template_w - 1, template_h - 1], [template_w - 1, 0]]).reshape(-1, 1, 2)
                # 将模板的四个角点坐标转换为原图中的位置
                dst_corners = cv2.perspectiveTransform(corners, M)
                source_with_rectangle = cv2.polylines(to_draw_rect, [np.int32(dst_corners)], False, (0, 255, 0), 2)
                cv2_utils.show_image(source_with_rectangle, win_name='source_with_rectangle')
        print(center_x, center_y)
        cv2.waitKey(0)


if __name__ == '__main__':
    _test_auto_cut_map()
    # win = gui_utils.get_win_by_name('崩坏：星穹铁道', active=True)
    # time.sleep(1)
    # calibrator = Calibrator(win, ch, mc)
    # calibrator._check_move_distance(save_screenshot=True)

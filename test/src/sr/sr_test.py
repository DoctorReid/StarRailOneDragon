import time

import cv2
import numpy as np
import pyautogui

import dev
import sr
from basic import gui_utils
from basic.img import cv2_utils, ImageMatcher, MatchResultList, MatchResult
from basic.img.cv2_matcher import CvImageMatcher
from dev import screenshot
from sr.config import ConfigHolder
from sr.map_cal import MapCalculator

ch = ConfigHolder()
mc = MapCalculator(config=ch)


def _test_standard_little_map(show: bool = False):
    """
    用标准图更新小地图位置
    :param show:
    :return:
    """
    screen = cv2_utils.read_image_with_alpha(dev.get_test_image('game_can_find_little_map.png'))
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
    image = cv2_utils.read_image_with_alpha(dev.get_test_image('game_can_find_little_map.png'))
    arrow_1 = mc.cut_little_map_arrow(image)
    cv2_utils.show_image(arrow_1)
    mc.cal_little_map_pos(image)
    arrow_2 = mc.cut_little_map_arrow(image)
    cv2_utils.show_image(arrow_2)


def _test_get_direction_by_screenshot():
    matcher: ImageMatcher = CvImageMatcher()
    matcher.load_template('loc_arrow', dev.get_test_image('loc_arrow.png'))
    game = cv2_utils.read_image_with_alpha(dev.get_test_image('game_can_find_little_map.png'))
    mc.cal_little_map_pos(game)
    print(mc.get_direction_by_screenshot(game, matcher, show_match_result=True))


def _test_match_little_map():
    """
    使用黑白图和灰度图进行小地图匹配的 效果不太行 代码先留着
    :return:
    """
    lm = cv2_utils.read_image_with_alpha(dev.get_test_image('little_map_stand.png'))
    y, x = lm.shape[:2]
    lm2 = cv2_utils.mark_area_as_transparent(lm, [(x // 2) - 20, (y // 2) - 20, 40, 40])
    # 创建掩码图像，将透明背景像素设置为零
    mask = np.where(lm2[..., 3] > 0, 255, 0).astype(np.uint8)
    # cv2_utils.show_image(mask)
    template = cv2_utils.binary_with_white_alpha(lm2)
    cv2_utils.show_image(template)
    mask2 = np.where(template[...] > 0, 0, 255).astype(np.uint8)
    # cv2_utils.show_image(mask2)
    final_mask = cv2.bitwise_and(mask, mask2)
    # cv2_utils.show_image(final_mask)

    m = sr.read_map_image('kjzht-jzcd')
    source = cv2_utils.binary_with_white_alpha(m)
    cv2_utils.show_image(source)

    result = cv2.matchTemplate(source, template, cv2.TM_CCOEFF_NORMED, mask=mask)
    match_result_list = MatchResultList()
    locations = np.where(result >= 0.4)  # 过滤低置信度的匹配结果
    max_result = None

    # 遍历所有匹配结果，并输出位置和置信度
    for pt in zip(*locations[::-1]):
        confidence = result[pt[1], pt[0]]  # 获取置信度
        current_result = MatchResult(confidence, pt[0], pt[1], x, y)
        match_result_list.append(current_result)
        if max_result is None or max_result.confidence < current_result.confidence:
            max_result = current_result
    print(match_result_list)
    cv2_utils.show_image(m, max_result)

    # 获取要覆盖图像的宽度和高度
    overlay_height, overlay_width = template.shape[:2]

    # 指定覆盖图像的位置
    x = max_result.x  # 起始横坐标
    y = max_result.y  # 起始纵坐标

    # 计算覆盖图像的结束坐标
    x_end = x + overlay_width
    y_end = y + overlay_height

    # 将覆盖图像放置到底图的指定位置
    source[y:y_end, x:x_end] = template[:, :]
    cv2_utils.show_image(source)

    # 将覆盖图像放置到底图的指定位置
    m[y:y_end, x:x_end] = lm[:, :]
    cv2_utils.show_image(m)


def _test_match_little_map2():
    lm = cv2_utils.read_image_with_alpha(dev.get_test_image('game2.png'))
    m = sr.read_map_image('kjzht-jzcd')
    print(mc.cal_character_pos(lm, m, show=True))
    cv2.waitKey(0)


if __name__ == '__main__':
    _test_match_little_map2()
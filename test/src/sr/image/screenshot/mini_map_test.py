import os

import cv2
import numpy as np
from cv2.typing import MatLike

from basic.img import cv2_utils
from basic.img.os import get_debug_image_dir, get_test_image, save_debug_image, get_debug_image
from sr.config.game_config import get_game_config
from sr.image.cv2_matcher import CvImageMatcher
from sr.image.image_holder import ImageHolder
from sr.image.sceenshot import mini_map


def _test_extract_arrow():
    dir = get_debug_image_dir()
    for filename in os.listdir(dir):
        screen = cv2_utils.read_image(os.path.join(dir, filename))
    # for i in range(5):
    #     screen = get_test_image('game%d' % (i+1))
        mm = mini_map.cut_mini_map(screen)
        cv2_utils.show_image(mm, win_name='mm')
        arrow = mini_map.extract_arrow(mm)
        cv2_utils.show_image(arrow, win_name='arrow')
        _, bw = cv2.threshold(arrow, 180, 255, cv2.THRESH_BINARY)
        cv2_utils.show_image(bw, win_name='bw')
        raw_arrow = cv2.bitwise_and(mm, mm, mask=bw)
        cv2_utils.show_image(raw_arrow, win_name='raw_arrow')

        cv2.waitKey(0)
        cv2.destroyAllWindows()


def _test_get_arrow_mask():
    screen = get_debug_image('1697036916493')
    mm = mini_map.cut_mini_map(screen)
    m, wm = mini_map.get_arrow_mask(mm)
    cv2_utils.show_image(m, win_name='m')
    cv2_utils.show_image(wm, win_name='wm')
    cv2.waitKey(0)


def _test_analyse_arrow_and_angle():
    screen = get_debug_image('1697036916493')
    mm = mini_map.cut_mini_map(screen)
    _, _, angle = mini_map.analyse_arrow_and_angle(mm, im)
    print(angle)


def _test_get_sp_mask_by_feature_match():
    screen: MatLike = get_debug_image('1696773991417')
    mm = mini_map.cut_mini_map(screen)
    info = mini_map.analyse_mini_map(mm, im)

    mini_map.get_sp_mask_by_feature_match(info, im, show=True)
    cv2.waitKey(0)


def _test_is_under_attack():
    for i in range(2):
        screen = get_test_image('%d' % (i + 1), sub_dir='under_attack')
        mm = mini_map.cut_mini_map(screen)
        print(mini_map.is_under_attack(mm, get_game_config().mini_map_pos, show=True))
        cv2.waitKey(0)


def _test_radio_mask():
    screen = get_debug_image('1697036262088')
    mm = mini_map.cut_mini_map(screen)
    road = np.zeros_like(mm, dtype=np.uint8)
    road[:,:] = [65,65,65]
    ans = cv2.subtract(mm, road)
    cv2_utils.show_image(ans, win_name='ans')
    cv2.waitKey(0)


def _test_get_enemy_road_mask():
    pass


def _test_cut_mini_map():
    screen = get_test_image('mm_arrow', sub_dir='mini_map')
    mm = mini_map.cut_mini_map(screen)
    save_debug_image(mm)
    # dir = get_debug_image_dir()
    # for x in os.listdir(dir):
    #     if not x.endswith('.png'):
    #         continue
    #     screen = cv2_utils.read_image(os.path.join(dir, x))
    #     mm = mc.cut_mini_map(screen)
    #     save_debug_image(mm)


if __name__ == '__main__':
    ih = ImageHolder()
    im = CvImageMatcher(ih)
    _test_cut_mini_map()
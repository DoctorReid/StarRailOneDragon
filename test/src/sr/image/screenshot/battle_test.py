import cv2

from basic.img import cv2_utils
from basic.img.os import get_test_image
from sr.image.cv2_matcher import CvImageMatcher
from sr.image.sceenshot import battle


def _test_get_battle_status():
    screen = get_test_image('mm_arrow')
    cv2_utils.show_image(screen[0:90, 1800:1900], win_name='icon_c"')
    print(battle.get_battle_status(screen, im))  # 1
    cv2.waitKey(0)


def _test_match_battle_ctrl():
    screen = get_test_image('all_off', sub_dir='battle')
    r = battle.match_battle_ctrl(screen, im, 'battle_ctrl_02', False)
    cv2_utils.show_image(screen, r, wait=0)


def _test_is_auto_battle_on():
    screen = get_test_image('all_off', sub_dir='battle')
    print(battle.is_auto_battle_on(screen, im))  # false
    screen = get_test_image('all_on', sub_dir='battle')
    print(battle.is_auto_battle_on(screen, im))  # true
    screen = get_test_image('all_on_2', sub_dir='battle')
    print(battle.is_auto_battle_on(screen, im))  # true


def _test_is_fast_battle_on():
    screen = get_test_image('all_off', sub_dir='battle')
    print(battle.is_fast_battle_on(screen, im))  # false
    screen = get_test_image('all_on', sub_dir='battle')
    print(battle.is_fast_battle_on(screen, im))  # true
    screen = get_test_image('all_on_2', sub_dir='battle')
    print(battle.is_fast_battle_on(screen, im))  # true


if __name__ == '__main__':
    im = CvImageMatcher()
    _test_is_auto_battle_on()
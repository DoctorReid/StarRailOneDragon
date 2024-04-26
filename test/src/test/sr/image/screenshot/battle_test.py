import cv2

from basic.img import cv2_utils
from basic.img.os import get_test_image, get_debug_image
from sr.image.cn_ocr_matcher import CnOcrMatcher
from sr.image.cv2_matcher import CvImageMatcher
from sr.image.sceenshot import battle


def _test_match_battle_ctrl():
    screen = get_test_image('all_off', sub_dir='battle')
    r = battle.match_battle_ctrl(screen, im, 'battle_ctrl_02', False)
    cv2_utils.show_image(screen, r, wait=0)


def _test_is_auto_battle_on():
    screen = get_test_image('all_off', sub_dir='battle')
    assert not battle.is_auto_battle_on(screen, im)  # false
    screen = get_test_image('all_on', sub_dir='battle')
    assert battle.is_auto_battle_on(screen, im)  # true
    screen = get_test_image('all_on_2', sub_dir='battle')
    assert battle.is_auto_battle_on(screen, im)  # true
    screen = get_test_image('all_on_3', sub_dir='battle')
    assert battle.is_auto_battle_on(screen, im)  # true
    screen = get_test_image('all_on_4', sub_dir='battle')
    assert battle.is_auto_battle_on(screen, im)  # true


def _test_is_fast_battle_on():
    screen = get_test_image('all_off', sub_dir='battle')
    assert not battle.is_fast_battle_on(screen, im)  # false
    screen = get_test_image('all_on', sub_dir='battle')
    assert battle.is_fast_battle_on(screen, im)  # true
    screen = get_test_image('all_on_2', sub_dir='battle')
    assert battle.is_fast_battle_on(screen, im)  # true
    screen = get_test_image('no_fast', sub_dir='battle')
    assert battle.is_fast_battle_on(screen, im)  # true
    screen = get_test_image('no_fast_2', sub_dir='battle')
    assert battle.is_fast_battle_on(screen, im)  # true
    screen = get_test_image('all_on_3', sub_dir='battle')
    assert battle.is_fast_battle_on(screen, im)  # true
    screen = get_test_image('all_on_4', sub_dir='battle')
    assert battle.is_fast_battle_on(screen, im)  # true


def _test_get_battle_result_str():
    screen = get_debug_image('_1700061743071')
    print(battle.get_battle_result_str(screen, ocr))
    cv2.waitKey(0)


if __name__ == '__main__':
    im = CvImageMatcher()
    ocr = CnOcrMatcher()
    _test_get_battle_result_str()
    # _test_get_battle_status()
    # _test_is_auto_battle_on()
    # _test_is_fast_battle_on()
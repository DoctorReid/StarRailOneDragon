import cv2

from basic.img import cv2_utils
from basic.img.os import get_test_image
from sr.image.cv2_matcher import CvImageMatcher
from sr.image.sceenshot import battle


def _test_get_battle_status():
    screen = get_test_image('mm_arrow')
    cv2_utils.show_image(screen[0:90, 1800:1900], win_name='icon_c"')
    print(battle.get_battle_status(screen, im))
    cv2.waitKey(0)


if __name__ == '__main__':
    im = CvImageMatcher()
    _test_get_battle_status()
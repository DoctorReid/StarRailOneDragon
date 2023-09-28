import cv2

from basic.img import cv2_utils
from basic.img.os import get_test_image
from sr.context import get_context, Context
from sr.image.sceenshot import large_map
from sr.image.sceenshot.icon import save_template_image


def _test_get_planet_name():
    screen = get_test_image('large_map_1')
    cv2_utils.show_image(screen[30:100, 90:250], win_name='cut', wait=0)
    print(large_map.get_planet(screen, ctx.ocr))


def _test_cut_minus():
    screen = get_test_image('large_map_1')

    cut, mask = large_map.cut_minus_or_plus(screen)
    cv2.waitKey(0)
    save_template_image(cut, 'minus', 'origin')
    save_template_image(mask, 'minus', 'mask')

    # cut, mask = large_map.cut_minus_or_plus(screen, minus=False)
    # cv2.waitKey(0)
    # save_template_image(cut, 'plus', 'origin')
    # save_template_image(mask, 'plus', 'mask')


if __name__ == '__main__':
    ctx = get_context('唯秘')
    _test_cut_minus()
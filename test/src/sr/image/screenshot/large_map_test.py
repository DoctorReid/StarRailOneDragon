from basic.img import cv2_utils
from basic.img.os import get_test_image
from sr.context import get_context, Context
from sr.image.sceenshot import large_map


def _test_get_planet_name(ctx: Context):
    screen = get_test_image('large_map_1')
    cv2_utils.show_image(screen[30:100, 90:250], win_name='cut', wait=0)
    print(large_map.get_planet(screen, ctx.ocr))


if __name__ == '__main__':
    ctx = get_context('唯秘')
    _test_get_planet_name(ctx)
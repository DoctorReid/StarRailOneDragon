from cv2.typing import MatLike

from basic.img import cv2_utils
from basic.img.os import get_test_image
from sr.context import Context, get_context
from sr.operation.unit.scale_large_map import ScaleLargeMap


def _test_click_scale():
    screen: MatLike = get_test_image('large_map_1')
    x1, y1, x2, y2 = ScaleLargeMap.rect
    source = screen[y1:y2, x1:x2]
    cv2_utils.show_image(source, win_name='source', wait=0)
    op.click_scale(screen, ctx.controller, ctx.im)


if __name__ == '__main__':
    ctx: Context = get_context('唯秘')
    op = ScaleLargeMap(5)
    _test_click_scale()
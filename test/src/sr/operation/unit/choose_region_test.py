import time

import cv2

from basic.img import cv2_utils
from basic.img.os import get_test_image
from sr import constants
from sr.context import get_context
from sr.operation.unit.choose_region import ChooseRegion


def _test_click_target_region():
    screen = get_test_image('large_map_2')
    x1, y1, x2, y2 = ChooseRegion.click_rect
    cv2.rectangle(screen, (x1, y1), (x2, y2), 0, 1)
    cv2_utils.show_image(screen, wait=0)
    assert op.click_target_region(screen, ctx.controller)


def _test_scroll_region_area():
    op.scroll_region_area(ctx.controller)
    time.sleep(1)
    op.scroll_region_area(ctx.controller, -1)


def _test_whole_operation():
    ctx.running = True
    ctx.controller.win.active()
    op.execute()


if __name__ == '__main__':
    ctx = get_context()
    op = ChooseRegion(constants.P2_YYL.cn, constants.R2_09_MDZ.cn)
    _test_click_target_region()
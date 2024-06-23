import time

import cv2

from basic.img import cv2_utils
from basic.img.os import get_test_image
from sr.const import map_const
from sr.const.map_const import Region
from sr.context.context import get_context
from sr.operation.unit.op_map import ChooseRegion


def _test_click_target_region():
    if real_game:
        ctx.running = True
        ctx.controller.init()
        op.execute()
    else:
        screen = get_test_image('large_map_2')
        x1, y1, x2, y2 = ChooseRegion.click_rect
        cv2.rectangle(screen, (x1, y1), (x2, y2), 0, 1)
        cv2_utils.show_image(screen, wait=0)
        assert op.click_target_region(screen)


def _test_scroll_region_area():
    op.scroll_region_area(ctx.controller)
    time.sleep(1)
    op.scroll_region_area(ctx.controller, -1)


def _test_click_target_level():
    screen = get_test_image('level', sub_dir='large_map')
    print(op.click_target_level(screen, '-1层'))
    cv2.waitKey(0)


def _test_whole_operation():
    ctx.running = True
    ctx.controller.init()
    op.execute()


if __name__ == '__main__':
    real_game = True
    ctx = get_context('唯秘')
    region: Region = map_const.P01_R03_B1
    op = ChooseRegion(ctx, region)
    _test_click_target_level()
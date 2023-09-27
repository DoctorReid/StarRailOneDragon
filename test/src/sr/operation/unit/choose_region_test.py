import time

from basic.img.os import get_test_image
from sr import constants
from sr.context import get_context
from sr.operation.unit.choose_region import ChooseRegion


def _test_click_target_region():
    screen = get_test_image('large_map_2')
    assert op.click_target_region(screen, ctx.controller)


def _test_scroll_region_area():
    op.scroll_region_area(ctx.controller)
    time.sleep(1)
    op.scroll_region_area(ctx.controller, -1)



if __name__ == '__main__':
    ctx = get_context('唯秘')
    op = ChooseRegion(constants.P1_KZJ.cn, constants.R1_02_JZCD.cn)
    _test_click_target_region()
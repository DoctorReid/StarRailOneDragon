import cv2

from basic.img import cv2_utils
from basic.img.os import get_test_image
from sr import constants
from sr.context import get_context, Context
from sr.operation.unit.choose_planet import ChoosePlanet


def _test_open_choose_planet(op: ChoosePlanet, ctx: Context):
    screen = get_test_image('large_map_2')
    x1, y1, x2, y2 = ChoosePlanet.xght_rect
    cv2.rectangle(screen, (x1,y1), (x2,y2), 0, 1)
    cv2_utils.show_image(screen, wait=0)
    print(op.open_choose_planet(screen, ctx.controller))  # 应该是 true


def _test_choose_planet():
    screen = get_test_image('choose_planet')
    print(op.choose_planet(screen, ctx.controller))  # 应该是 true


def _test_whole_operation():
    op.execute()


if __name__ == '__main__':
    ctx = get_context()
    ctx.running = True
    ctx.controller.win.active()
    op = ChoosePlanet(constants.P2_YYL.cn)
    _test_whole_operation()
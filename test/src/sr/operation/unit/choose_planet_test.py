import cv2
import pyautogui

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


def _test_choose_planet(op: ChoosePlanet, ctx: Context):
    screen = get_test_image('choose_planet')
    print(op.choose_planet(screen, ctx.controller))  # 应该是 true


if __name__ == '__main__':
    # ctx = get_context('唯秘')
    # op = ChoosePlanet(constants.P1_KZJ.cn)
    # _test_open_choose_planet(op, ctx)
    pyautogui.click()
    pyautogui.scroll(100)
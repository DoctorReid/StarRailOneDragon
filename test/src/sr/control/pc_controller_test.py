import pyautogui

from sr.control.pc_controller import PcController
from sr.win import Window


def _test_turn_by_distance():
    x1 = pyautogui.position().x
    ctx.controller.turn_by_distance(100)
    x2 = pyautogui.position().x
    print(x2 - x1)


def _test_move_towards():
    ctx.controller.init()
    ctx.controller.move_towards((0, 0), (0, 90), 270)



if __name__ == '__main__':
    ctrl = PcController(Window('微信'), None)
import pyautogui

from sr.context import Context, get_context


def _test_turn_by_distance():
    x1 = pyautogui.position().x
    ctx.controller.turn_by_distance(100)
    x2 = pyautogui.position().x
    print(x2 - x1)


def _test_move_towards():
    ctx.controller.init()
    ctx.controller.move_towards((0, 0), (0, 90), 270)


if __name__ == '__main__':
    ctx: Context = get_context('唯秘')
    _test_turn_by_distance()
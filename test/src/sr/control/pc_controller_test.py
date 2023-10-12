import pyautogui

from sr.context import Context, get_context


def _test_turn_by_distance():
    print(pyautogui.position())
    ctx.controller.turn_by_distance(600)
    print(pyautogui.position())


def _test_move_towards():
    ctx.controller.init()
    ctx.controller.move_towards((0, 0), (0, 90), 270)


if __name__ == '__main__':
    ctx: Context = get_context()
    _test_move_towards()
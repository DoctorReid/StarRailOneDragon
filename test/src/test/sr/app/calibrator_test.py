from basic.img.os import get_debug_image
from sr.app.calibrator import Calibrator
from sr.context.context import get_context


def _test_check_mini_map_pos():
    screen = get_debug_image('1696613369880')
    app._check_mini_map_pos(screen)


def _test_check_turning_rate():
    ctx.running = True
    ctx.controller.init()
    ans = app._check_turning_rate()

def _test_whole_app():
    app._execute_one_round()


if __name__ == '__main__':
    ctx = get_context()
    app = Calibrator(ctx)
    _test_check_turning_rate()
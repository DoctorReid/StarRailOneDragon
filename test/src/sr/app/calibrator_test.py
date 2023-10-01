from basic.img.os import get_test_image
from sr.app.calibrator import Calibrator
from sr.context import get_context


def _test_check_mini_map_pos():
    screen = get_test_image('mm_arrow')
    app._check_mini_map_pos(screen)


def _test_check_turning_rate():
    ctx.running = True
    ctx.controller.init()
    app._check_turning_rate()


def _test_whole_app():
    app.run()


if __name__ == '__main__':
    ctx = get_context()
    app = Calibrator(ctx)
    _test_check_turning_rate()
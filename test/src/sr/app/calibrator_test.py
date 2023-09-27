from basic.img.os import get_test_image
from sr.app.calibrator import Calibrator
from sr.context import get_context


def _test_check_little_map_pos(app: Calibrator):
    screen = get_test_image('mm_arrow')
    app._check_little_map_pos(screen)


if __name__ == '__main__':
    ctx = get_context(win_title='唯秘')
    app = Calibrator(ctx)
    _test_check_little_map_pos(app)
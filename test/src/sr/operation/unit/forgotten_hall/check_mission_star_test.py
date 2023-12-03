from basic.img.os import get_debug_image
from sr.context import get_context
from sr.operation.unit.forgotten_hall import get_mission_star
from sr.operation.unit.forgotten_hall.check_mission_star import CheckMissionStar


def _test_get_mission_star():
    screen = get_debug_image('_1701586867255')
    get_mission_star(ctx, 1, screen)


if __name__ == '__main__':
    ctx = get_context()
    ctx.init_ocr_matcher()
    ctx.init_image_matcher()

    op = CheckMissionStar(ctx, 1)
    _test_get_mission_star()
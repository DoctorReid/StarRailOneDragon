from basic.img.os import get_debug_image
from sr.context import get_context
from sr.image.sceenshot import mini_map
from sr.operation.unit.forgotten_hall.auto_fight_in_forgotten_hall import FindEnemyAndFightInForgottenHall


def _test_find_enemy_pos():
    screen = get_debug_image('_1701532194037')
    mm = mini_map.cut_mini_map(screen)
    print(op._find_enemy_pos(mm))


if __name__ == '__main__':
    ctx = get_context()
    ctx.init_image_matcher()

    op = FindEnemyAndFightInForgottenHall(ctx)
    _test_find_enemy_pos()

from sr import constants
from sr.constants.map import Planet, Region, TransportPoint
from sr.context import get_context
from sr.operation.unit.move_directly import MoveDirectly


def _test_whole_op():
    ctx.running = True
    ctx.controller.init()
    op.execute()


if __name__ == '__main__':
    ctx = get_context()
    r: Region = constants.map.P01_R02_JZCD
    tp: TransportPoint = constants.map.P01_R02_TP01_JKS
    large_map = ctx.ih.get_large_map(r, map_type='origin')
    lm_info = ctx.map_cal.analyse_large_map(large_map)

    op = MoveDirectly(ctx, lm_info, target=(650, 200), start=tp.lm_pos, save_screenshot=False)
    _test_whole_op()
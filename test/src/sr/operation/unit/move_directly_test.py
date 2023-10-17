from sr import constants
from sr.constants.map import Planet, Region, TransportPoint
from sr.context import get_context
from sr.image.sceenshot import large_map
from sr.operation.unit.move_directly import MoveDirectly


def _test_whole_op():
    ctx.running = True
    ctx.controller.init()
    op.execute()


if __name__ == '__main__':
    ctx = get_context()
    r: Region = constants.map.P01_R02_JZCD
    tp: TransportPoint = constants.map.P01_R02_SP01_JKS
    lm_info = large_map.analyse_large_map(r, ctx.ih)

    op = MoveDirectly(ctx, lm_info, target=(650, 200), start=tp.lm_pos)
    _test_whole_op()
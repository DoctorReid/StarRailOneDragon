from sr.const import map_const
from sr.const.map_const import Region, TransportPoint
from sr.context import get_context
from sr.image.sceenshot import large_map
from sr.operation.unit.move_directly import MoveDirectly


def _test_whole_op():
    ctx.running = True
    ctx.controller.init()
    op.execute()


if __name__ == '__main__':
    ctx = get_context()
    r: Region = map_const.P01_R02
    tp: TransportPoint = map_const.P01_R02_SP01
    lm_info = large_map.analyse_large_map(r, ctx.ih)

    op = MoveDirectly(ctx, lm_info, target=(650, 200), start=tp.lm_pos)
    _test_whole_op()
from basic import Point
from sr.const import map_const
from sr.const.map_const import Region, TransportPoint
from sr.context.context import get_context
from sr.operation.unit.move import MoveDirectly


def _test_whole_op():
    ctx.running = True
    ctx.controller.init()
    op.execute()


if __name__ == '__main__':
    ctx = get_context()
    r: Region = map_const.P01_R02
    tp: TransportPoint = map_const.P01_R02_SP01
    lm_info = ctx.ih.get_large_map(r)

    op = MoveDirectly(ctx, lm_info, target=Point(650, 200), start=tp.tp_pos)
    _test_whole_op()
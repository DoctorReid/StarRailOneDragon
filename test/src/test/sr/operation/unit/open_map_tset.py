from sr.context import get_context, Context
from sr.operation.unit.open_map import OpenMap


def _test_whole_operation():
    ctx.controller.win.active()
    op.execute()


if __name__ == '__main__':
    ctx: Context = get_context()
    ctx.running = True
    op = OpenMap()
    _test_whole_operation()

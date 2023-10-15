from sr.app.world_patrol import WorldPatrol, WorldPatrolRoute
from sr.context import Context, get_context


def _test_read_yaml():
    WorldPatrolRoute('P01_R02_R01')


def _test_run_one_route():
    ctx.running = True
    ctx.controller.init()
    app.first = False
    app.run_one_route('P01_R03_R03')


if __name__ == '__main__':
    ctx: Context = get_context()
    app = WorldPatrol(ctx)
    _test_run_one_route()
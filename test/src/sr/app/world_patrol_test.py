from sr.app.world_patrol import WorldPatrol, WorldPatrolRoute
from sr.context import Context, get_context


def _test_read_yaml():
    WorldPatrolRoute('P01_R02_R01')


def _test_run_one_route():
    ctx.running = True
    ctx.controller.init()
    # app.run_one_route('P01_R02_R01')
    app.run_one_route('P01_R03_R02')


if __name__ == '__main__':
    ctx: Context = get_context()
    app = WorldPatrol(ctx)
    _test_run_one_route()
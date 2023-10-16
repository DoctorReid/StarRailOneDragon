from sr.app.world_patrol import WorldPatrol, WorldPatrolRoute
from sr.context import Context, get_context


def _test_read_yaml():
    WorldPatrolRoute('P01_R02_R01')


def _test_run_one_route():
    ctx.init_all(renew=True)
    ctx.start_running()
    ctx.controller.init()
    app.first = False
    app.init_app()
    app.run_one_route('P02_R03_R01')


if __name__ == '__main__':
    ctx: Context = get_context()
    app = WorldPatrol(ctx)
    _test_run_one_route()
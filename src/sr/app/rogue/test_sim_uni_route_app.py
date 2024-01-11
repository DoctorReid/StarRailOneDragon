from basic.i18_utils import gt
from sr.app import Application2
from sr.app.rogue import SimUniRoute
from sr.app.rogue.run_sim_uni_route import RunSimUniRoute
from sr.context import Context
from sr.operation.combine import StatusCombineOperationNode
from sr.operation.unit.rogue.reset_sim_uni_level import ResetSimUniLevel


class TestSimUniRouteApp(Application2):

    def __init__(self, ctx: Context, route: SimUniRoute):
        """
        测试模拟宇宙路线
        :param ctx:
        :param route:
        """
        super().__init__(ctx, op_name='%s %s' % (gt('模拟宇宙', 'ui'), gt('测试路线', 'ui')),
                         nodes=[
                             StatusCombineOperationNode('重进', ResetSimUniLevel(ctx)),
                             StatusCombineOperationNode('执行路线', RunSimUniRoute(ctx, route)),
                         ])
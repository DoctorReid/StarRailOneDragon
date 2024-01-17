from typing import Optional

from basic.i18_utils import gt
from sr.app import Application2
from sr.app.sim_uni.sim_uni_route_holder import match_best_sim_uni_route
from sr.app.sim_uni.sim_uni_run_world import SimUniRunWorld
from sr.context import Context
from sr.image.sceenshot import mini_map
from sr.operation import Operation, OperationSuccess
from sr.operation.combine import StatusCombineOperationNode
from sr.sim_uni.op.reset_sim_uni_level import ResetSimUniLevel
from sr.sim_uni.sim_uni_const import SimUniPath, SimUniLevelTypeEnum, SimUniLevelType
from sr.sim_uni.sim_uni_priority import SimUniBlessPriority, SimUniNextLevelPriority
from sr.sim_uni.sim_uni_route import SimUniRoute


class TestSimUniRouteApp(Application2):

    def __init__(self, ctx: Context, uni_num: int, level_type: SimUniLevelType,
                 route: Optional[SimUniRoute]):
        """
        测试模拟宇宙路线
        :param ctx:
        :param route:
        """
        bless_priority = SimUniBlessPriority(SimUniPath.PROPAGATION.value)
        next_level_priority = SimUniNextLevelPriority(SimUniLevelTypeEnum.EVENT.value.type_id)
        super().__init__(
            ctx, op_name='%s %s' % (gt('模拟宇宙', 'ui'), gt('测试路线', 'ui')),
            nodes=[
                StatusCombineOperationNode('判断重进', op_func=self._check_route),
                StatusCombineOperationNode('挑战',
                                           SimUniRunWorld(ctx, uni_num,
                                                          bless_priority=bless_priority,
                                                          next_level_priority=next_level_priority)),
            ])

        self.uni_num: int = uni_num
        self.level_type: SimUniLevelType = level_type
        self.route: SimUniRoute = route

    def _check_route(self) -> Operation:
        if not self.level_type.need_route:
            return OperationSuccess(self.ctx)

        screen = self.screenshot()
        mm = mini_map.cut_mini_map(screen)
        route = match_best_sim_uni_route(self.uni_num, self.level_type, mm)

        if route is not None and route.uid == self.route.uid:
            return OperationSuccess(self.ctx)
        else:
            return ResetSimUniLevel(self.ctx)

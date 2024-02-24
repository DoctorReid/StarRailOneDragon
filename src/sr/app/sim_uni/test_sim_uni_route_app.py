from typing import Optional, ClassVar

from basic.i18_utils import gt
from sr.app.application_base import Application2
from sr.app.sim_uni.sim_uni_route_holder import match_best_sim_uni_route
from sr.app.sim_uni.sim_uni_run_world import SimUniRunWorld
from sr.app.sim_uni.sim_universe_app import get_record
from sr.context import Context
from sr.image.sceenshot import mini_map
from sr.operation import Operation, OperationResult, StateOperationNode, OperationOneRoundResult, \
    StateOperationEdge
from sr.sim_uni.op.reset_sim_uni_level import ResetSimUniLevel
from sr.sim_uni.sim_uni_config import SimUniAppConfig, get_sim_uni_app_config
from sr.sim_uni.sim_uni_const import SimUniLevelType
from sr.sim_uni.sim_uni_route import SimUniRoute


class TestSimUniRouteApp(Application2):

    STATUS_NO_ROUTE_MATCHED: ClassVar[str] = '匹配不到路线'

    def __init__(self, ctx: Context, uni_num: int, level_type: SimUniLevelType,
                 route: Optional[SimUniRoute]):
        """
        测试模拟宇宙路线
        :param ctx:
        :param route:
        """
        edges = []

        check = StateOperationNode('判断重进', self._check_route)
        reset = StateOperationNode('重进', op=ResetSimUniLevel(ctx))
        edges.append(StateOperationEdge(check, reset, status=TestSimUniRouteApp.STATUS_NO_ROUTE_MATCHED))

        challenge = StateOperationNode('挑战', self._run_world)
        edges.append(StateOperationEdge(check, challenge, ignore_status=True))
        edges.append(StateOperationEdge(reset, challenge))

        super().__init__(
            ctx, op_name='%s %s' % (gt('模拟宇宙', 'ui'), gt('测试路线', 'ui')),
            edges=edges
        )

        self.config: SimUniAppConfig = get_sim_uni_app_config()
        self.uni_num: int = uni_num
        self.level_type: SimUniLevelType = level_type
        self.route: SimUniRoute = route

    def _check_route(self) -> OperationOneRoundResult:
        screen = self.screenshot()
        mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
        route = match_best_sim_uni_route(self.uni_num, self.level_type, mm)

        if route is not None and route.uid == self.route.uid:
            return Operation.round_success()
        else:
            return Operation.round_success(status=TestSimUniRouteApp.STATUS_NO_ROUTE_MATCHED)

    def _run_world(self) -> OperationOneRoundResult:
        uni_challenge_config = self.config.get_challenge_config(self.uni_num)
        op = SimUniRunWorld(self.ctx, self.uni_num,
                            config=uni_challenge_config,
                            op_callback=self._on_world_done
                            )
        return Operation.round_by_op(op.execute())

    def _on_world_done(self, op_result: OperationResult):
        run_record = get_record()
        if op_result.success:
            run_record.add_times()

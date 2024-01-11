from typing import Optional

from basic import Point
from basic.i18_utils import gt
from sr.app.rogue import SimUniRoute, SimUniRouteOperation
from sr.const import operation_const
from sr.context import Context
from sr.operation import StateOperation, StateOperationNode, OperationOneRoundResult, StateOperationEdge, Operation, \
    OperationResult
from sr.operation.unit.enter_auto_fight import EnterAutoFight
from sr.operation.unit.rogue.move_in_sim_uni import MoveDirectlyInSimUni


class RunSimUniRoute(StateOperation):

    def __init__(self, ctx: Context, route: SimUniRoute):
        """
        按照特定路线执行
        """
        self.route: SimUniRoute = route
        self.op_idx: int = -1
        self.current_pos: Point = self.route.start_pos

        op_node = StateOperationNode('执行路线指令', self._next_op)
        edges = [StateOperationEdge(op_node, op_node, status='next')]
        super().__init__(ctx,
                         op_name='%s %s %s' % (
                             gt('模拟宇宙', 'ui'),
                             gt('执行路线', 'ui'),
                             route.display_name
                         ),
                         edges=edges,
                         specified_start_node=op_node)

    def _init_before_execute(self):
        """
        执行前的初始化 注意初始化要全面 方便一个指令重复使用
        """
        super()._init_before_execute()
        self.op_idx = -1
        self.current_pos: Point = self.route.start_pos

    def _next_op(self) -> OperationOneRoundResult:
        """
        获取下一个具体的指令
        :return:
        """
        self.op_idx += 1

        if self.op_idx >= len(self.route.op_list):
            return Operation.round_fail('非法的指令下标')

        current_op: SimUniRouteOperation = self.route.op_list[self.op_idx]
        next_op: Optional[SimUniRouteOperation] = self.route.op_list[self.op_idx + 1] if self.op_idx + 1 < len(self.route.op_list) else None

        op_result: Optional[OperationResult] = None
        if current_op['op'] in [operation_const.OP_MOVE, operation_const.OP_SLOW_MOVE]:
            op_result = self.move(current_op, next_op)
        elif current_op['op'] == operation_const.OP_PATROL:
            op_result = self.patrol()

        if op_result is None:
            return Operation.round_fail(status='未知指令')
        elif op_result.success:  # 进入下一个指令
            return Operation.round_wait(status='next', data=op_result.data)
        else:
            return Operation.round_fail(status=op_result.status, data=op_result.data)

    def move(self, current_op: SimUniRouteOperation, next_op: Optional[SimUniRouteOperation]) -> OperationResult:
        """
        按坐标进行移动
        :param current_op: 当前指令
        :param next_op: 下一个指令
        :return:
        """
        next_pos = Point(current_op['data'][0], current_op['data'][1])
        next_is_move = next_op is not None and next_op['op'] in [operation_const.OP_MOVE, operation_const.OP_SLOW_MOVE]
        op = MoveDirectlyInSimUni(self.ctx, self.ctx.ih.get_large_map(self.route.region),
                                  start=self.current_pos, target=next_pos,
                                  stop_afterwards=not next_is_move)
        op_result = op.execute()

        if op_result.success:
            self.current_pos = next_pos

        return op_result

    def patrol(self) -> OperationResult:
        """
        主动战斗
        :return:
        """
        op = EnterAutoFight(self.ctx)
        return op.execute()

from typing import Optional

from basic import Point
from basic.i18_utils import gt
from sr.const import operation_const
from sr.context import Context
from sr.operation import Operation, \
    OperationResult, OperationFail, OperationSuccess
from sr.operation.combine import StatusCombineOperation2, StatusCombineOperationNode, StatusCombineOperationEdge2
from sr.sim_uni.op.battle_in_sim_uni import SimUniEnterFight
from sr.sim_uni.op.move_in_sim_uni import MoveDirectlyInSimUni
from sr.sim_uni.sim_uni_priority import SimUniBlessPriority
from sr.sim_uni.sim_uni_route import SimUniRouteOperation, SimUniRoute


class SimUniRunRoute(StatusCombineOperation2):

    def __init__(self, ctx: Context, route: SimUniRoute,
                 bless_priority: Optional[SimUniBlessPriority] = None):
        """
        按照特定路线执行
        """
        self.route: SimUniRoute = route
        self.op_idx: int = -1
        self.current_pos: Point = self.route.start_pos
        self.bless_priority: SimUniBlessPriority = bless_priority

        op_node = StatusCombineOperationNode('执行路线指令', op_func=self._next_op)
        finish_node = StatusCombineOperationNode('结束', OperationSuccess(ctx))
        go_next = StatusCombineOperationEdge2(op_node, op_node, ignore_status=True)
        go_finish = StatusCombineOperationEdge2(op_node, finish_node, status='执行结束')

        edges = [go_next, go_finish]

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

    def _next_op(self) -> Operation:
        """
        获取下一个具体的指令
        :return:
        """
        self.op_idx += 1

        if self.op_idx >= len(self.route.op_list):
            return OperationSuccess(self.ctx, '执行结束')

        current_op: SimUniRouteOperation = self.route.op_list[self.op_idx]
        next_op: Optional[SimUniRouteOperation] = self.route.op_list[self.op_idx + 1] if self.op_idx + 1 < len(self.route.op_list) else None

        if current_op['op'] in [operation_const.OP_MOVE, operation_const.OP_SLOW_MOVE]:
            return self.move(current_op, next_op)
        elif current_op['op'] == operation_const.OP_PATROL:
            return SimUniEnterFight(self.ctx, bless_priority=self.bless_priority)
        else:
            return OperationFail(self.ctx, status='未知指令')

    def move(self, current_op: SimUniRouteOperation, next_op: Optional[SimUniRouteOperation]) -> Operation:
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
                                  stop_afterwards=not next_is_move,
                                  op_callback=self._update_pos,
                                  bless_priority=self.bless_priority
                                  )
        return op

    def _update_pos(self, op_result: OperationResult):
        """
        更新坐标
        :param op_result:
        :return:
        """
        if op_result.success:
            self.current_pos = op_result.data

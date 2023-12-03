from typing import List

from basic.i18_utils import gt
from sr.context import Context
from sr.operation import Operation
from sr.operation.combine import StatusCombineOperation, StatusCombineOperationEdge
from sr.operation.unit.forgotten_hall.auto_fight_in_forgotten_hall import AutoFightInForgottenHall
from sr.operation.unit.forgotten_hall.move_to_enemy import MoveToEnemy
from sr.operation.unit.forgotten_hall.wait_in_session import WaitNodeStart


class NodeFight(StatusCombineOperation):

    def __init__(self, ctx: Context,
                 is_first_node: bool):
        """
        需要已经在忘却之庭节点内的页面
        移动到敌人身边后
        使用秘技并攻击敌人
        完成战斗后 返回战斗结果
        :param ctx:
        :param is_first_node:
        """
        ops: List[Operation] = []
        edges: List[StatusCombineOperationEdge] = []

        node_start = WaitNodeStart(ctx, is_first_node, timeout_seconds=15)  # 等待节点开始
        ops.append(node_start)

        move = MoveToEnemy(ctx)  # 移动进入战斗
        ops.append(move)
        edges.append(StatusCombineOperationEdge(op_from=node_start, op_to=move))

        fight = AutoFightInForgottenHall(ctx)  # 进入战斗
        ops.append(fight)
        edges.append(StatusCombineOperationEdge(op_from=move, op_to=fight))

        super().__init__(ctx, ops, edges, op_name=gt('忘却之庭 节点挑战', 'ui'))

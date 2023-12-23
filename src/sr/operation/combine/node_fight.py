from typing import List, Optional, Callable

from basic.i18_utils import gt
from sr.const.character_const import Character
from sr.context import Context
from sr.operation import Operation, OperationResult
from sr.operation.combine import StatusCombineOperation, StatusCombineOperationEdge
from sr.operation.unit.forgotten_hall.auto_fight_in_forgotten_hall import AutoFightInForgottenHall
from sr.operation.unit.forgotten_hall.enter_fight_in_fh import EnterFightInForgottenHall
from sr.operation.unit.forgotten_hall.move_to_enemy import MoveToEnemy
from sr.operation.unit.forgotten_hall.wait_in_node import WaitNodeStart


class NodeFight(StatusCombineOperation):

    def __init__(self, ctx: Context,
                 is_first_node: bool,
                 team: Optional[List[Character]] = None,
                 op_callback: Optional[Callable[[OperationResult], None]] = None
                 ):
        """
        需要已经在忘却之庭节点内的页面
        移动到敌人身边后
        使用秘技并攻击敌人
        完成战斗后 返回战斗结果
        :param ctx:
        :param is_first_node: 是否第一个节点 第一个节点开始时会显示一个buff
        :param team: 当前节点使用的配队 无传入时自动识别 但不准
        :param op_callback: 节点结束后的回调
        """
        ops: List[Operation] = []
        edges: List[StatusCombineOperationEdge] = []

        node_start = WaitNodeStart(ctx, is_first_node, timeout_seconds=15)  # 等待节点开始
        ops.append(node_start)

        move = MoveToEnemy(ctx)  # 移动进入战斗
        ops.append(move)
        edges.append(StatusCombineOperationEdge(op_from=node_start, op_to=move))

        enter_fight = EnterFightInForgottenHall(ctx, character_list=team)  # 使用秘技并进入战斗
        ops.append(enter_fight)
        edges.append(StatusCombineOperationEdge(op_from=move, op_to=enter_fight))

        auto_fight = AutoFightInForgottenHall(ctx)  # 进入战斗
        ops.append(auto_fight)
        edges.append(StatusCombineOperationEdge(op_from=enter_fight, op_to=auto_fight))

        super().__init__(ctx, ops, edges, op_name=gt('忘却之庭 节点挑战', 'ui'),
                         op_callback=op_callback)

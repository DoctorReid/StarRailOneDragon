from typing import List, Optional, Union

from pydantic import BaseModel

from sr.context import Context
from sr.operation import Operation, OperationResult, OperationOneRoundResult


class CombineOperation(Operation):
    """
    一堆指令的组合，单个指令失败就会终止
    """
    def __init__(self, ctx: Context, ops: List[Operation], op_name: str = ''):
        """
        :param ctx:
        :param ops: 指令列表
        :param op_name: 指令名称
        """
        super().__init__(ctx, try_times=len(ops), op_name=op_name)
        self.ops: List[Operation] = ops

    def _execute_one_round(self) -> int:
        if self.ops is None:  # 初始化指令失败
            return Operation.FAIL
        op = self.ops[self.op_round - 1]
        result = op.execute()
        if not result.success:
            return Operation.FAIL

        return Operation.RETRY if self.op_round < len(self.ops) else Operation.SUCCESS


class StatusCombineOperationEdge(BaseModel):
    """
    指令节点
    """

    op_from_id: int
    """上一个指令"""

    op_to_id: int
    """下一个指令"""

    success: bool
    """是否成功才执行下一个指令"""

    status: Optional[str] = None
    """
    执行下一个指令的条件状态 
    一定要完全一样才会执行 包括None
    """

    ignore_status: bool
    """
    是否忽略状态进行下一个指令
    一个指令应该最多只有一条边忽略返回状态
    忽略返回状态只有在所有需要匹配的状态都匹配不到时才会用做兜底
    """

    def __init__(self, op_from: Operation, op_to: Operation,
                 success: bool = True,
                 status: Optional[str] = None,
                 ignore_status: bool = True):
        super().__init__(op_from_id=id(op_from),
                         op_to_id=id(op_to),
                         success=success,
                         status=status,
                         ignore_status=False if status is not None else ignore_status)


class StatusCombineOperation(Operation):
    """
    带有状态转移的组合指令
    """

    def __init__(self, ctx: Context,
                 ops: List[Operation],
                 edges: List[StatusCombineOperationEdge],
                 try_times: int = 2, op_name: str = '', timeout_seconds: float = -1,
                 start_op: Optional[Operation] = None):
        Operation.__init__(self, ctx,
                           try_times=try_times,
                           op_name=op_name,
                           timeout_seconds=timeout_seconds)

        self._start_op: Optional[Operation] = start_op  # 开始指令
        self._op_map: dict[int, Operation] = {}  # 指令集合
        self._op_edges_map: dict[int, List[StatusCombineOperationEdge]] = {}  # 下一个指令的集合
        self._multiple_start: bool = False  # 多个开始节点
        self._current_op: Optional[Operation] = None  # 当前指令

        self._init_from_edges(ops, edges)

    def _init_from_edges(self, ops: List[Operation], edges: List[StatusCombineOperationEdge]):
        for op in ops:
            self._op_map[id(op)] = op

        op_in_map: dict[int, int] = {}  # 入度

        for edge in edges:
            from_id = edge.op_from_id
            if from_id not in self._op_edges_map:
                self._op_edges_map[from_id] = []
            self._op_edges_map[from_id].append(edge)

            to_idx = edge.op_to_id
            if to_idx not in op_in_map:
                op_in_map[to_idx] = 0
            op_in_map[to_idx] = op_in_map[to_idx] + 1

        if self._start_op is None:  # 没有指定开始节点时 自动判断
            # 找出入度为0的开始点
            for edge in edges:
                from_id = edge.op_from_id
                if from_id not in op_in_map or op_in_map[from_id] == 0:
                    if self._start_op is not None and id(self._start_op) != from_id:
                        self._multiple_start = True
                    self._start_op = self._op_map[from_id]

    def _init_before_execute(self):
        super()._init_before_execute()
        self._current_op = self._start_op

    def execute(self) -> OperationResult:
        if self._multiple_start:
            return Operation.op_fail('多个开始指令')
        return Operation.execute(self)

    def _execute_one_round(self) -> OperationOneRoundResult:
        current_op_result: OperationResult = self._current_op.execute()

        if not current_op_result.success:  # 指令执行失败
            return Operation.round_fail(current_op_result.status)

        edges = self._op_edges_map.get(id(self._current_op))
        if edges is None:  # 没有下一个节点了 已经结束了
            return Operation.round_success(current_op_result.status)

        next_op_id: Optional[int] = None
        final_next_op_id: Optional[int] = None  # 兜底指令
        for edge in edges:
            if edge.success != current_op_result.success:
                continue

            if edge.ignore_status:
                final_next_op_id = edge.op_to_id

            if edge.status is None and current_op_result.status is None:
                next_op_id = edge.op_to_id
                break
            elif edge.status is None or current_op_result.status is None:
                continue
            elif edge.status == current_op_result.status:
                next_op_id = edge.op_to_id

        next_op: Optional[Operation] = None
        if next_op_id is not None:
            next_op = self._op_map[next_op_id]
        elif final_next_op_id is not None:
            next_op = self._op_map[final_next_op_id]

        if next_op is None:  # 没有下一个节点了 已经结束了
            return Operation.round_success(current_op_result.status)

        self._current_op = next_op
        return Operation.round_wait(current_op_result.status)

from typing import List, Optional, Callable

from basic.log_utils import log
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


class StatusCombineOperationEdge:

    def __init__(self, op_from: Operation, op_to: Operation,
                 success: bool = True,
                 status: Optional[str] = None,
                 ignore_status: bool = True):
        """
        指令节点
        :param op_from:
        :param op_to:
        :param success:
        :param status:
        :param ignore_status:
        """

        self.op_from_id: int = id(op_from)
        """上一个指令"""

        self.op_to_id: int = id(op_to)
        """下一个指令"""

        self.success: bool = success
        """是否成功才执行下一个指令"""

        self.status: Optional[str] = status
        """
        执行下一个指令的条件状态 
        一定要完全一样才会执行 包括None
        """

        self.ignore_status: bool = False if status is not None else ignore_status
        """
        是否忽略状态进行下一个指令
        一个指令应该最多只有一条边忽略返回状态
        忽略返回状态只有在所有需要匹配的状态都匹配不到时才会用做兜底
        """


class StatusCombineOperation(Operation):
    """
    带有状态转移的组合指令
    """

    def __init__(self, ctx: Context,
                 ops: List[Operation],
                 edges: List[StatusCombineOperationEdge],
                 op_name: str = '', timeout_seconds: float = -1,
                 start_op: Optional[Operation] = None,
                 op_callback: Optional[Callable[[OperationResult], None]] = None
                 ):
        Operation.__init__(self, ctx,
                           try_times=1,  # 组合指令运行 作为一个框架不应该有出错重试
                           op_name=op_name,
                           timeout_seconds=timeout_seconds,
                           op_callback=op_callback)

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


class StatusCombineOperationNode:

    def __init__(self, node_id: str, op: Optional[Operation] = None, op_func: Optional[Callable[[], Operation]] = None):

        self.node_id: str = node_id
        """节点ID"""

        self.op_func: Optional[Callable[[], Operation]] = op_func
        """该节点对应指令的生成器 与具体指令只需其中一个"""

        self.op: Optional[Operation] = op
        """该节点对应的指令 与指令指令生成器只需其中一个"""

    def get_operation(self) -> Operation:
        """
        获取具体的指令
        :return:
        """
        return self.op_func() if self.op is None else self.op


class StatusCombineOperationEdge2:

    def __init__(self, node_from: StatusCombineOperationNode, node_to: StatusCombineOperationNode,
                 success: bool = True, status: Optional[str] = None, ignore_status: bool = True):

        self.node_from: StatusCombineOperationNode = node_from
        """上一个指令"""

        self.node_to: StatusCombineOperationNode = node_to
        """下一个指令"""

        self.success: bool = success
        """是否成功才执行下一个指令"""

        self.status: Optional[str] = status
        """
        执行下一个指令的条件状态 
        一定要完全一样才会执行 包括None
        """

        self.ignore_status: bool = False if status is not None else ignore_status
        """
        是否忽略状态进行下一个指令
        一个指令应该最多只有一条边忽略返回状态
        忽略返回状态只有在所有需要匹配的状态都匹配不到时才会用做兜底
        """


class StatusCombineOperation2(Operation):

    def __init__(self, ctx: Context, op_name: str,
                 timeout_seconds: float = -1,
                 edges: Optional[List[StatusCombineOperationEdge2]] = None,
                 specified_start_node: Optional[StatusCombineOperationNode] = None):
        Operation.__init__(self, ctx,
                           try_times=1,  # 组合指令运行 作为一个框架不应该有出错重试
                           op_name=op_name,
                           timeout_seconds=timeout_seconds,
                           )
        self.edge_list: List[StatusCombineOperationEdge2] = []
        """边列表"""

        self._node_edges_map: dict[str, List[StatusCombineOperationEdge2]] = {}
        """下一个节点的集合"""

        self._node_map: dict[str, StatusCombineOperationNode] = {}
        """节点"""

        self._specified_start_node: Optional[StatusCombineOperationNode] = specified_start_node
        """指定的开始节点 当网络存在环时 需要自己指定"""

        self._start_node: Optional[StatusCombineOperationNode] = None
        """其实节点 初始化后才会有"""

        self._multiple_start: bool = False
        """是否有多个开始节点 属于异常情况"""

        self._current_node: Optional[StatusCombineOperationNode] = None
        """当前执行的节点"""

        if edges is not None:
            for edge in edges:
                self._register_edge(edge)

    def _register_edge(self, edge: StatusCombineOperationEdge2):
        """
        注册一条边
        不会只有一个节点的情况 只有一个节点无需使用这个类
        :param edge:
        :return:
        """
        if self.executing:
            log.error('%s 正在执行 无法进行节点注册', self.display_name)
            return
        self.edge_list.append(edge)

    def set_specified_start_node(self, start_node: StatusCombineOperationNode):
        """
        设置开始节点
        :param start_node:
        :return:
        """
        if self.executing:
            log.error('%s 正在执行 无法设置开始节点', self.display_name)
            return
        self._specified_start_node = start_node

    def _init_network(self):
        """
        进行节点网络的初始化
        :return:
        """
        self._node_edges_map = {}
        self._node_map = {}
        self._start_node = None
        self._multiple_start = False

        op_in_map: dict[str, int] = {}  # 入度

        for edge in self.edge_list:
            from_id = edge.node_from.node_id
            if from_id not in self._node_edges_map:
                self._node_edges_map[from_id] = []
            self._node_edges_map[from_id].append(edge)

            to_id = edge.node_to.node_id
            if to_id not in op_in_map:
                op_in_map[to_id] = 0
            op_in_map[to_id] = op_in_map[to_id] + 1

            self._node_map[from_id] = edge.node_from
            self._node_map[to_id] = edge.node_to

        if self._specified_start_node is None:  # 没有指定开始节点时 自动判断
            # 找出入度为0的开始点
            for edge in self.edge_list:
                from_id = edge.node_from.node_id
                if from_id not in op_in_map or op_in_map[from_id] == 0:
                    if self._start_node is not None and self._start_node.node_id != from_id:
                        self._start_node = None
                        break
                    self._start_node = self._node_map[from_id]
        else:
            self._start_node = self._specified_start_node

    def _init_before_execute(self):
        """
        执行前的初始化 注意初始化要全面 方便一个指令重复使用
        """
        super()._init_before_execute()
        self._init_network()
        self._current_node = self._start_node

    def _execute_one_round(self) -> OperationOneRoundResult:
        if self._current_node is None:
            return Operation.round_fail('无开始节点')
        current_op = self._current_node.get_operation()
        current_op_result: OperationResult = current_op.execute()

        edges = self._node_edges_map.get(self._current_node.node_id)
        if edges is None:  # 没有下一个节点了 已经结束了
            return self.round_result_by_op(current_op_result)

        next_node_id: Optional[str] = None
        final_next_node_id: Optional[str] = None  # 兜底指令
        for edge in edges:
            if edge.success != current_op_result.success:
                continue

            if edge.ignore_status:
                final_next_node_id = edge.node_to.node_id

            if edge.status is None and current_op_result.status is None:
                next_node_id = edge.node_to.node_id
                break
            elif edge.status is None or current_op_result.status is None:
                continue
            elif edge.status == current_op_result.status:
                next_node_id = edge.node_to.node_id

        next_node: Optional[StatusCombineOperationNode] = None
        if next_node_id is not None:
            next_node = self._node_map[next_node_id]
        elif final_next_node_id is not None:
            next_node = self._node_map[final_next_node_id]

        if next_node is None:  # 没有下一个节点了 已经结束了
            return self.round_result_by_op(current_op_result)

        self._current_node = next_node
        return Operation.round_wait(current_op_result.status)

    def round_result_by_op(self, op_result: OperationResult) -> OperationOneRoundResult:
        if op_result.success:
            return self.round_success(op_result.status)
        else:
            return self.round_fail(op_result.status)
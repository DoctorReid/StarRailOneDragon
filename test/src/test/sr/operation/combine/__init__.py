import unittest
from typing import Optional

import test
from sr.context import Context, get_context
from sr.operation import Operation, OperationOneRoundResult, OperationResult
from sr.operation.combine import StatusCombineOperation2, StatusCombineOperationNode, StatusCombineOperationEdge2


class SimpleOp1(Operation):

    def __init__(self, ctx: Context, op_callback):
        super().__init__(ctx, op_name='测试指令1', op_callback=op_callback)

    def _execute_one_round(self) -> OperationOneRoundResult:
        return self.round_success('1')


class SimpleOp2(Operation):

    last_value: Optional[int] = None

    def __init__(self, ctx: Context, last_value: Optional[int] = None):
        super().__init__(ctx, op_name='测试指令2')
        self.last_value = last_value

    def _execute_one_round(self) -> OperationOneRoundResult:
        return self.round_success(str(self.last_value + 1))


class CombineOp(StatusCombineOperation2):

    last_value: Optional[int] = None

    def __init__(self, ctx: Context):
        super().__init__(ctx, op_name='测试组合指令')
        node1 = StatusCombineOperationNode(node_id='op1', op=SimpleOp1(self.ctx, self.op1_callback))
        node2 = StatusCombineOperationNode(node_id='op2', op_func=self.op2_func)
        self._register_edge(StatusCombineOperationEdge2(node_from=node1, node_to=node2, ignore_status=True))

    def handle_init(self) -> Optional[OperationOneRoundResult]:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        可以返回初始化后判断的结果
        - 成功时跳过本指令
        - 失败时立刻返回失败
        - 不返回时正常运行本指令
        """
        self.last_value = None

    def op1_callback(self, op_result: OperationResult):
        if op_result.success:
            self.last_value = int(op_result.status)

    def op2_func(self) -> Operation:
        return SimpleOp2(self.ctx, self.last_value)


class TestStatusCombineOperation2(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

        ctx = get_context()
        ctx.running = 1
        self.op = CombineOp(ctx)

    def test_execute(self):
        op_result = self.op.execute()
        self.assertEquals('2', op_result.status)

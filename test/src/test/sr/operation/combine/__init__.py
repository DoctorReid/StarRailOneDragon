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
        return Operation.round_success('1')


class SimpleOp2(Operation):

    last_value: Optional[int] = None

    def __init__(self, ctx: Context, last_value: Optional[int] = None):
        super().__init__(ctx, op_name='测试指令2')
        self.last_value = last_value

    def _execute_one_round(self) -> OperationOneRoundResult:
        return Operation.round_success(str(self.last_value + 1))


class CombineOp(StatusCombineOperation2):

    last_value: Optional[int] = None

    def __init__(self, ctx: Context):
        super().__init__(ctx, op_name='测试组合指令')
        node1 = StatusCombineOperationNode(node_id='op1', op=SimpleOp1(self.ctx, self.op1_callback))
        node2 = StatusCombineOperationNode(node_id='op2', op_func=self.op2_func)
        self._register_edge(StatusCombineOperationEdge2(node_from=node1, node_to=node2, ignore_status=True))

    def _init_before_execute(self):
        super()._init_before_execute()
        self.last_value = None

    def op1_callback(self, op_result: OperationResult):
        if op_result.success:
            self.last_value = int(op_result.status)

    def op2_func(self) -> Operation:
        return SimpleOp2(self.ctx, self.last_value)


class TestStatusCombineOperation2(unittest.TestCase, test.SrTestBase):

    def setUp(self):
        test.SrTestBase.__init__(self, __file__)

        ctx = get_context()
        ctx.running = 1
        self.op = CombineOp(ctx)

    def test_execute(self):
        op_result = self.op.execute()
        self.assertEquals('2', op_result.status)

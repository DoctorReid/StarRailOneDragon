import unittest
import test
from sr.context import Context, get_context
from sr.operation import Operation, OperationOneRoundResult, OperationResult, StateOperation, StateOperationNode, \
    StateOperationEdge


class SimpleOperation(Operation):

    def __init__(self, ctx: Context, op_callback):
        super().__init__(ctx, op_name='测试指令', op_callback=op_callback)

    def _execute_one_round(self) -> OperationOneRoundResult:
        return Operation.round_success()


class TestOperation(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

    def test_operation(self):
        self.op.ctx.running = 1
        op_result = self.op.execute()
        self.assertTrue(op_result.success)
        self.assertTrue(self.callback_result)

    def _op_callback(self, result: OperationResult):
        self.callback_result = result.success


class SimpleStateOperation(StateOperation):

    def __init__(self, ctx: Context):
        """
        当初始数为1时
          1 + 1 = 2
          2 * 2 = 4
          4 - 1 = 3
        当初始数为2时
          2 + 1 = 3
          3 * 3 = 9
        :param ctx:
        """
        edges = []

        add_one = StateOperationNode('加1', self.add_one)
        mul_two = StateOperationNode('乘2', self.add_one)
        edges.append(StateOperationEdge(add_one, mul_two, status='2'))

        mul_three = StateOperationNode('乘3', self.mul_three)
        edges.append(StateOperationEdge(add_one, mul_three, ignore_status=True))

        del_one = StateOperationNode('减1', self.del_one)
        edges.append(StateOperationEdge(mul_two, del_one, status='4'))

        super().__init__(ctx, op_name='simple', edges=edges)
        self.num: int = 1

    def add_one(self):
        self.num += 1
        return Operation.round_success(status=str(self.num))

    def mul_two(self):
        self.num *= 2
        return Operation.round_success(status=str(self.num))

    def mul_three(self):
        self.num *= 3
        return Operation.round_success(status=str(self.num))

    def del_one(self):
        self.num -= 1
        return Operation.round_success(status=str(self.num))

    def del_two(self):
        self.num -= 2
        return Operation.round_success(status=str(self.num))


class TestStateOperation(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

        self.op = SimpleStateOperation(get_context())

    def test_execute(self):
        self.op.ctx.running = 1

        self.op.num = 1
        op_result = self.op.execute()
        self.assertTrue(op_result.success)
        self.assertEqual('3', op_result.status)

        self.op.num = 2
        op_result = self.op.execute()
        self.assertTrue(op_result.success)
        self.assertEqual('9', op_result.status)



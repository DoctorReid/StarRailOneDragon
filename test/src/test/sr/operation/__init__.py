import unittest
import test
from sr.context import Context, get_context
from sr.operation import Operation, OperationOneRoundResult, OperationResult


class SimpleOperation(Operation):

    def __init__(self, ctx: Context, op_callback):
        super().__init__(ctx, op_name='测试指令', op_callback=op_callback)

    def _execute_one_round(self) -> OperationOneRoundResult:
        return Operation.round_success()


class TestOperation(unittest.TestCase, test.SrTestBase):

    def setUp(self):
        test.SrTestBase.__init__(self, __file__)

        self.op = SimpleOperation(get_context(), self._op_callback)
        self.callback_result = False

    def test_operation(self):
        self.op.ctx.running = 1
        op_result = self.op.execute()
        self.assertTrue(op_result.success)
        self.assertTrue(self.callback_result)

    def _op_callback(self, result: OperationResult):
        self.callback_result = result.success

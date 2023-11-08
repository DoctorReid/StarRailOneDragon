from typing import List

from sr.context import Context
from sr.operation import Operation


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
        if not op.execute() and not op.allow_fail:
            return Operation.FAIL

        return Operation.RETRY if self.op_round < len(self.ops) else Operation.SUCCESS

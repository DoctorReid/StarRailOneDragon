from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from sr_od.context.sr_context import SrContext
from sr_od.operations.sr_operation import SrOperation


class GameplayInteract(SrOperation):

    def __init__(self, ctx: SrContext, seconds: int = 0):
        """
        玩法交互
        - 翁法罗斯 - 时光倒流
        :param ctx:
        :param seconds: 按键持续秒数
        """
        SrOperation.__init__(self, ctx, op_name=gt('玩法交互'))

        self.seconds: int = seconds

    @operation_node(name='按键', is_start_node=True)
    def press(self) -> OperationRoundResult:
        self.ctx.controller.gameplay_interact(self.seconds)
        return self.round_success()

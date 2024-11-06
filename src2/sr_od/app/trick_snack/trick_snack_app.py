from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from sr_od.app.sr_application import SrApplication
from sr_od.context.sr_context import SrContext
from sr_od.operations.custom_combine_op.custom_combine_op import CustomCombineOp


class TrickSnackApp(SrApplication):

    def __init__(self, ctx: SrContext):
        SrApplication.__init__(self, ctx, 'trick_snack', op_name=gt('奇巧零食', 'ui'),
                               run_record=ctx.trick_snack_run_record)

    @operation_node(name='执行自定义指令', is_start_node=True)
    def run_op(self) -> OperationRoundResult:
        op = CustomCombineOp(self.ctx, 'buy_trick_snack')
        return self.round_by_op_result(op.execute())

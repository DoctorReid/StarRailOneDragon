from basic.i18_utils import gt
from sr.app.application_base import Application
from sr.context.context import Context
from sr.custom_combine_op.custom_combine_op import CustomCombineOp
from sr.operation import StateOperationNode


class TrickSnackApp(Application):

    def __init__(self, ctx: Context):
        super().__init__(ctx, op_name=gt('奇巧零食', 'ui'),
                         run_record=ctx.trick_snack_run_record)

    def add_edges_and_nodes(self) -> None:
        """
        初始化前 添加边和节点 由子类实行
        :return:
        """
        self.param_start_node = StateOperationNode('购买合成奇巧零食',
                                                   op=CustomCombineOp(self.ctx, 'buy_trick_snack'))

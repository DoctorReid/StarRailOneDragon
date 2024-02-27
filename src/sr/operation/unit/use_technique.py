from basic.i18_utils import gt
from sr.context import Context
from sr.operation import Operation, OperationOneRoundResult


class UseTechnique(Operation):

    def __init__(self, ctx: Context):
        """
        需在大世界页面中使用
        用当前角色使用秘技
        :param ctx:
        """
        super().__init__(ctx, try_times=2, op_name=gt('施放秘技', 'ui'))

    def _execute_one_round(self) -> OperationOneRoundResult:
        self.ctx.controller.use_technique()
        return Operation.round_success()

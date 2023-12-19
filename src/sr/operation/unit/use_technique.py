from basic.i18_utils import gt
from sr.context import Context
from sr.operation import Operation, OperationOneRoundResult
from sr.operation.unit.back_to_world import BackToWorld


class UseTechnique(Operation):

    def __init__(self, ctx: Context):
        """
        需在大世界页面中使用
        使用秘技
        :param ctx:
        """
        super().__init__(ctx, try_times=2, op_name=gt('施放秘技', 'ui'))

    def _execute_one_round(self) -> OperationOneRoundResult:
        world = BackToWorld(self.ctx)  # 确保当前在大世界
        world_result = world.execute()
        if not world_result.success:
            return Operation.round_retry(world_result.status)

        self.ctx.controller.use_technique()
        return Operation.round_success()

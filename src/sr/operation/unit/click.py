from basic import Point
from basic.i18_utils import gt
from sr.context import Context
from sr.operation import Operation, OperationOneRoundResult


class Click(Operation):

    def __init__(self, ctx: Context, point: Point):
        """
        点击指定坐标
        :param ctx: 上下文
        :param point: 坐标
        """
        super().__init__(ctx, op_name='%s %s' % (gt('点击', 'ui'), point))
        self.point: Point = point

    def _execute_one_round(self) -> OperationOneRoundResult:
        if self.ctx.controller.click(self.point):
            return Operation.round_success()
        else:
            return Operation.round_retry('click_fail')

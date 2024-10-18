from cv2.typing import MatLike

from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log
from sr_od.context.sr_context import SrContext
from sr_od.operations.sr_operation import SrOperation


class OpenPhoneMenu(SrOperation):

    """
    打开菜单 = 看到开拓等级
    看不到的情况只需要不停按 ESC 即可
    """

    def __init__(self, ctx: SrContext):
        super().__init__(ctx, op_name=gt('打开菜单', 'ui'))

    @operation_node(name='画面识别', node_max_retry_times=10, is_start_node=True)
    def check_screen(self) -> OperationRoundResult:
        screen: MatLike = self.screenshot()

        result = self.round_by_find_area(screen, '菜单', '开拓等级')
        if result.is_success:
            return self.round_success()
        else:
            self.ctx.controller.esc()
            log.info('尝试打开菜单')
            return self.round_retry(status='未在菜单画面', wait=2)

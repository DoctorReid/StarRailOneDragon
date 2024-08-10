from cv2.typing import MatLike

from basic.i18_utils import gt
from basic.log_utils import log
from sr.context.context import Context
from sr.operation import Operation, OperationOneRoundResult
from sr.screen_area.screen_phone_menu import ScreenPhoneMenu


class OpenPhoneMenu(Operation):

    """
    打开菜单 = 看到开拓等级
    看不到的情况只需要不停按 ESC 即可
    """

    def __init__(self, ctx: Context):
        super().__init__(ctx, try_times=10, op_name=gt('打开菜单', 'ui'))

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen: MatLike = self.screenshot()
        area = ScreenPhoneMenu.TRAILBLAZE_LEVEL_PART.value

        if self.find_area(area, screen):
            return self.round_success()

        self.ctx.controller.esc()
        log.info('尝试打开菜单')

        return self.round_retry(status='未在菜单画面', wait=2)

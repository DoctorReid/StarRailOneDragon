import time

from cv2.typing import MatLike

from basic.i18_utils import gt
from sr.context import Context
from sr.image.sceenshot import phone_menu
from sr.operation import Operation


class OpenPhoneMenu(Operation):

    """
    打开菜单 = 看到开拓等级
    看不到的情况只需要不停按 ESC 即可
    """

    def __init__(self, ctx: Context):
        super().__init__(ctx, try_times=10, op_name=gt('打开菜单', 'ui'))

    def _execute_one_round(self) -> int:
        screen: MatLike = self.screenshot()

        if phone_menu.in_phone_menu(screen, self.ctx.ocr):
            return Operation.SUCCESS

        self.ctx.controller.esc()
        time.sleep(1)

        return Operation.RETRY

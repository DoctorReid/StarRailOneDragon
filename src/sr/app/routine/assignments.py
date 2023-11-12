import time

from cv2.typing import MatLike

from basic.i18_utils import gt
from basic.img import MatchResult
from basic.log_utils import log
from sr.app import Application
from sr.const import phone_menu_const
from sr.context import Context
from sr.image.sceenshot import phone_menu
from sr.operation import Operation
from sr.operation.unit.claim_assignment import ClaimAssignment
from sr.operation.unit.open_phone_menu import OpenPhoneMenu


class Assignments(Application):

    def __init__(self, ctx: Context):
        super().__init__(ctx, op_name=gt('委托', 'ui'))
        self.phase: int = 0

    def _execute_one_round(self) -> int:
        if self.phase == 0:
            op = OpenPhoneMenu(self.ctx)
            if op.execute():
                self.phase += 1
                return Operation.WAIT
            else:
                return Operation.FAIL
        elif self.phase == 1:
            screen: MatLike = self.screenshot()
            result: MatchResult = phone_menu.get_phone_menu_item_pos(screen, self.ctx.im, phone_menu_const.ASSIGNMENTS, alert=True)
            if result is None:
                log.info('检测不到委托红点 跳过')
                return Operation.SUCCESS
            else:
                self.ctx.controller.click(result.center)
                self.phase += 1
                time.sleep(1)
                return Operation.WAIT
        elif self.phase == 2:
            op = ClaimAssignment(self.ctx)
            if op.execute():
                self.phase += 1
                return Operation.WAIT
            else:
                return Operation.FAIL
        elif self.phase == 3:  # 领取完返回菜单
            op = OpenPhoneMenu(self.ctx)
            r = op.execute()
            if not r:
                return Operation.FAIL
            else:
                return Operation.SUCCESS
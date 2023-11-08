import time

from cv2.typing import MatLike

from basic.i18_utils import gt
from basic.img import MatchResult
from basic.log_utils import log
from sr.app import Application
from sr.context import Context
from sr.image.sceenshot import phone_menu
from sr.operation import Operation
from sr.operation.unit.open_phone_menu import OpenPhoneMenu


class SupportCharacter(Application):

    """
    收取支援角色奖励
    """

    def __init__(self, ctx: Context):
        super().__init__(ctx, op_name=gt('支援角色奖励', 'ui'))
        self.phase: int = 3

    def _execute_one_round(self) -> int:
        if self.phase == 0:  # 打开菜单
            op = OpenPhoneMenu(self.ctx)
            if op.execute():
                self.phase += 1
                return Operation.WAIT
            else:
                return Operation.FAIL
        elif self.phase == 1:  # 检测省略号红点并点击
            screen: MatLike = self.screenshot()
            result: MatchResult = phone_menu.get_phone_menu_ellipsis_pos(screen, self.ctx.im, alert=True)
            if result is None:
                log.info('检测不到省略号红点 跳过')
                return Operation.SUCCESS
            else:
                self.ctx.controller.click(result.center())
                self.phase += 1
                time.sleep(1)
                return Operation.WAIT
        elif self.phase == 2:  # 检测漫游签证红点并点击
            screen: MatLike = self.screenshot()
            result: MatchResult = phone_menu.get_phone_menu_ellipsis_item_pos(screen, self.ctx.im, self.ctx.ocr, '漫游签证', alert=True)
            if result is None:
                log.info('检测不到漫游签证红点 跳过')
                return Operation.SUCCESS
            else:
                self.ctx.controller.click(result.center())
                self.phase += 1
                time.sleep(1)
                return Operation.WAIT
        elif self.phase == 3:  # 领取支援角色奖励
            screen: MatLike = self.screenshot()
            result: MatchResult = phone_menu.get_alert_pos(screen, self.ctx.im, phone_menu.SUPPORT_CHARACTER_PART).max
            if result is None:
                log.info('检测不到支援角色红点 跳过')
                return Operation.SUCCESS
            else:
                self.ctx.controller.click(result.center() + phone_menu.SUPPORT_CHARACTER_PART.left_top())
                self.phase += 1
                time.sleep(1)
                return Operation.WAIT
        elif self.phase == 4:  # 领取完返回菜单
            op = OpenPhoneMenu(self.ctx)
            r = op.execute()
            if not r:
                return Operation.FAIL
            else:
                return Operation.SUCCESS
import time
from typing import Optional

from cv2.typing import MatLike

from basic.i18_utils import gt
from basic.img import MatchResult
from basic.log_utils import log
from sr.app import Application, AppRunRecord, AppDescription, register_app
from sr.context import Context
from sr.image.sceenshot import phone_menu
from sr.operation import Operation
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu

SUPPORT_CHARACTER = AppDescription(cn='支援角色', id='support_character')
register_app(SUPPORT_CHARACTER)


class SupportCharacterRecord(AppRunRecord):

    def __init__(self):
        super().__init__(SUPPORT_CHARACTER.id)


support_character_record: Optional[SupportCharacterRecord] = None


def get_record() -> SupportCharacterRecord:
    global support_character_record
    if support_character_record is None:
        support_character_record = SupportCharacterRecord()
    return support_character_record


class SupportCharacter(Application):

    """
    收取支援角色奖励
    2023-11-12 中英文最高画质测试通过
    """

    def __init__(self, ctx: Context):
        super().__init__(ctx, op_name=gt('支援角色奖励', 'ui'),
                         run_record=get_record())
        self.phase: int = 0

    def _execute_one_round(self) -> int:
        if self.phase == 0:  # 打开菜单
            op = OpenPhoneMenu(self.ctx)
            if op.execute().result:
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
                self.ctx.controller.click(result.center)
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
                self.ctx.controller.click(result.center)
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
                self.ctx.controller.click(result.center + phone_menu.SUPPORT_CHARACTER_PART.left_top)
                self.phase += 1
                time.sleep(1)
                return Operation.WAIT
        elif self.phase == 4:  # 领取完返回菜单
            op = OpenPhoneMenu(self.ctx)
            r = op.execute().result
            if not r:
                return Operation.FAIL
            else:
                return Operation.SUCCESS

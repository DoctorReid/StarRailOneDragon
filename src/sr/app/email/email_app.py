import time
from typing import ClassVar

from cv2.typing import MatLike

from basic import Rect, str_utils
from basic.i18_utils import gt
from basic.img import MatchResult, cv2_utils
from basic.log_utils import log
from sr.app.application_base import Application
from sr.const import phone_menu_const
from sr.context import Context
from sr.image.sceenshot import phone_menu
from sr.operation import Operation
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu


class Email(Application):

    """
    收取邮件奖励 但不会删除邮件
    2023-11-12 中英文最高画质测试通过
    """

    CLAIM_ALL_RECT: ClassVar[Rect] = Rect(390, 960, 520, 1000)  # 全部领取

    def __init__(self, ctx: Context):
        super().__init__(ctx, op_name=gt('收取邮件奖励', 'ui'),
                         run_record=ctx.email_run_record)

        self.phase: int = 0

    def _execute_one_round(self) -> int:
        if self.phase == 0:  # 打开菜单
            op = OpenPhoneMenu(self.ctx)
            r = op.execute().success
            if not r:
                return Operation.FAIL
            else:
                self.phase += 1
                time.sleep(1)
                return Operation.WAIT
        elif self.phase == 1:  # 检测邮件红点
            screen: MatLike = self.screenshot()
            email_result: MatchResult = phone_menu.get_phone_menu_item_pos_at_right(screen, self.ctx.im, phone_menu_const.EMAILS, alert=True)
            if email_result is None:
                log.info('检测不到邮件红点 跳过')
                return Operation.SUCCESS
            else:
                self.ctx.controller.click(email_result.center)
                self.phase += 1
                time.sleep(1)
                return Operation.WAIT
        elif self.phase == 2:  # 检测并点击全部领取
            screen: MatLike = self.screenshot()
            claim_all_part, _ = cv2_utils.crop_image(screen, Email.CLAIM_ALL_RECT)
            ocr_result = self.ctx.ocr.ocr_for_single_line(claim_all_part, strict_one_line=True)
            if str_utils.find_by_lcs(gt('全部领取', 'ocr'), ocr_result, percent=0.5):
                self.ctx.controller.click(Email.CLAIM_ALL_RECT.center)
                self.phase += 1
                time.sleep(1)
                return Operation.WAIT
            else:
                return Operation.FAIL
        elif self.phase == 3:  # 领取完返回菜单
            op = OpenPhoneMenu(self.ctx)
            r = op.execute().success
            if not r:
                return Operation.FAIL
            else:
                return Operation.SUCCESS

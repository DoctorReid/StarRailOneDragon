import time
from typing import ClassVar

from cv2.typing import MatLike

from basic import Rect, str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.context import Context
from sr.operation import Operation


class ClickChallengeConfirm(Operation):
    """
    点击挑战的确认
    目前使用的场景有
    - 历战回响 - 没有剩余次数
    """
    CONFIRM_BTN_RECT: ClassVar[Rect] = Rect(1020, 660, 1330, 690)  # 确认按钮

    STATUS_NO_DIALOG: ClassVar[str] = 'no_dialog'

    def __init__(self, ctx: Context):
        super().__init__(ctx, try_times=4, op_name=gt('确认挑战', 'ui'))

    def _execute_one_round(self) -> int:
        screen: MatLike = self.screenshot()
        part, _ = cv2_utils.crop_image(screen, ClickChallengeConfirm.CONFIRM_BTN_RECT)
        ocr_result = self.ctx.ocr.ocr_for_single_line(part, strict_one_line=True)

        if str_utils.find_by_lcs(gt('确认' 'ocr'), ocr_result, 0.1):
            if self.ctx.controller.click(ClickChallengeConfirm.CONFIRM_BTN_RECT.center):
                return Operation.SUCCESS

        time.sleep(0.5)
        return Operation.RETRY

    def _retry_fail_to_success(self, retry_status: str) -> str:
        """
        这个动作允许失败 为了兼容不知道是否会出现对话框的场景
        :retry_status: 重试返回的状态
        :return:
        """
        return ClickChallengeConfirm.STATUS_NO_DIALOG

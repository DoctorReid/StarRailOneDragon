import time
from typing import ClassVar

from cv2.typing import MatLike

from basic import Rect, str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.context import Context
from sr.operation import Operation


class ClickChallenge(Operation):

    """
    点击挑战
    """

    CHALLENGE_BTN_RECT: ClassVar[Rect] = Rect(1360, 950, 1890, 1010)

    def __init__(self, ctx: Context):
        super().__init__(ctx, try_times=5, op_name=gt('点击挑战', 'ui'))  # 交互后打开副本页面大概需要3秒 所以重试设置5次

    def _execute_one_round(self) -> int:
        screen: MatLike = self.screenshot()
        part, _ = cv2_utils.crop_image(screen, ClickChallenge.CHALLENGE_BTN_RECT)
        ocr_result = self.ctx.ocr.ocr_for_single_line(part, strict_one_line=True)
        if str_utils.find_by_lcs(gt('挑战', 'ocr'), ocr_result, percent=0.3):
            if self.ctx.controller.click(ClickChallenge.CHALLENGE_BTN_RECT.center):
                return Operation.SUCCESS

        time.sleep(1)
        return Operation.RETRY

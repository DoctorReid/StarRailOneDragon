import time
from typing import ClassVar

from cv2.typing import MatLike

from basic import Rect, str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.context.context import Context
from sr.operation import Operation


class ClickStartChallenge(Operation):

    """
    点击【开始挑战】
    """

    START_CHALLENGE_BTN_RECT: ClassVar[Rect] = Rect(1500, 960, 1840, 1010)

    def __init__(self, ctx: Context):
        super().__init__(ctx, op_name=gt('点击挑战', 'ui'))

    def _execute_one_round(self) -> int:
        screen: MatLike = self.screenshot()
        part, _ = cv2_utils.crop_image(screen, ClickStartChallenge.START_CHALLENGE_BTN_RECT)
        ocr_result = self.ctx.ocr.ocr_for_single_line(part, strict_one_line=True)
        if str_utils.find_by_lcs(gt('开始挑战', 'ocr'), ocr_result, percent=0.5):
            if self.ctx.controller.click(ClickStartChallenge.START_CHALLENGE_BTN_RECT.center):
                return Operation.SUCCESS

        time.sleep(1)
        return Operation.RETRY

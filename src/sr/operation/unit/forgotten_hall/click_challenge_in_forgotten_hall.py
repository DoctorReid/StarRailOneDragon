from typing import ClassVar

from basic import Rect
from basic.i18_utils import gt
from sr.context import Context
from sr.operation import Operation, OperationOneRoundResult


class ClickChallengeInForgottenHall(Operation):

    START_CHALLENGE_BTN_RECT: ClassVar[Rect] = Rect(1500, 960, 1840, 1010)

    def __init__(self, ctx: Context):
        """
        点击【开始挑战】
        """
        super().__init__(ctx, op_name=gt('逐光捡金点击挑战', 'ui'))

    def _execute_one_round(self) -> OperationOneRoundResult:
        click = self.ocr_and_click_one_line('混沌回忆', ClickChallengeInForgottenHall.START_CHALLENGE_BTN_RECT)

        if click == Operation.OCR_CLICK_SUCCESS:
            return Operation.round_success()
        else:
            return Operation.round_retry('cant_click_challenge')
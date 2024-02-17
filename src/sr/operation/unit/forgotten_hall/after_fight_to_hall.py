from typing import ClassVar

from basic import Rect
from basic.i18_utils import gt
from sr.context import Context
from sr.operation import Operation, OperationOneRoundResult
from sr.operation.unit.forgotten_hall.wait_in_hall import WaitInHall


class AfterFightToHall(Operation):

    BACK_BTN_1_RECT: ClassVar[Rect] = Rect(630, 920, 870, 975)
    BACK_BTN_2_RECT: ClassVar[Rect] = Rect(790, 920, 1140, 975)

    def __init__(self, ctx: Context):
        """
        需要已经在逐光捡金节点战斗结算的页面
        点击【返回逐光捡金】
        :param ctx: 上下文
        """
        super().__init__(ctx, op_name=gt('逐光捡金 结算后返回', 'ui'))
        self.phase: int = 0

    def _execute_one_round(self) -> OperationOneRoundResult:
        if self.phase == 0:
            screen = self.screenshot()
            for rect in [AfterFightToHall.BACK_BTN_1_RECT, AfterFightToHall.BACK_BTN_2_RECT]:
                click = self.ocr_and_click_one_line('返回逐光捡金', rect, screen)
                if click == Operation.OCR_CLICK_SUCCESS:
                    self.phase += 1
                    return Operation.round_wait()
        elif self.phase == 1:
            wait = WaitInHall(self.ctx)
            if wait.execute().success:
                return Operation.round_success()

        return Operation.round_retry()

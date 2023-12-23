from typing import ClassVar, Union

from basic import Rect
from basic.i18_utils import gt
from sr.context import Context
from sr.image.sceenshot import secondary_ui
from sr.image.sceenshot.secondary_ui import TITLE_SYNTHESIZE
from sr.operation import Operation, OperationOneRoundResult


class DoSynthesize(Operation):

    SYNTHESIZE_BTN_RECT: ClassVar[Rect] = Rect(1086, 942, 1293, 991)
    CONFIRM_BTN_RECT: ClassVar[Rect] = Rect(1090, 680, 1251, 723)
    EMPTY_BTN_RECT: ClassVar[Rect] = Rect(790, 919, 1136, 972)

    def __init__(self, ctx: Context):
        """
        进行合成
        需要在合成页面 并已经选择好物品后使用
        """
        super().__init__(ctx, op_name=gt('合成', 'ui'), try_times=5)

        self.phase: int = 0

    def _init_before_execute(self):
        """
        执行前的初始化 注意初始化要全面 方便一个指令重复使用
        """
        super()._init_before_execute()
        self.phase = 0

    def _execute_one_round(self) -> OperationOneRoundResult:
        if self.phase == 0:  # 需要在合成页面
            screen = self.screenshot()
            if secondary_ui.in_secondary_ui(screen, self.ctx.ocr, TITLE_SYNTHESIZE.cn):
                self.phase += 1
                return Operation.round_wait()
            else:
                return Operation.round_retry('未在合成页面', 1)
        elif self.phase == 1:  # 点击合成
            click = self.ocr_and_click_one_line('合成', DoSynthesize.SYNTHESIZE_BTN_RECT)
            if click == Operation.OCR_CLICK_SUCCESS:
                self.phase += 1
                return Operation.round_wait(wait=1.5)
            else:
                return Operation.round_retry('点击合成失败', wait=1)
        elif self.phase == 2:  #
            click = self.ocr_and_click_one_line('确认', DoSynthesize.CONFIRM_BTN_RECT)
            if click == Operation.OCR_CLICK_SUCCESS:
                self.phase += 1
                return Operation.round_wait(wait=3)
            else:
                return Operation.round_retry('点击合成失败', wait=1)
        elif self.phase == 3:  #
            click = self.ocr_and_click_one_line('点击空白处关闭', DoSynthesize.EMPTY_BTN_RECT)
            if click == Operation.OCR_CLICK_SUCCESS:
                return Operation.round_success(wait=1.5)
            else:
                return Operation.round_retry('点击空白处关闭失败', wait=1)
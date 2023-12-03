import time
from typing import Union, ClassVar

from basic import Rect
from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.context import Context
from sr.operation import Operation, OperationOneRoundResult


class WaitNodeStart(Operation):

    EXIT_BTN: ClassVar[Rect] = Rect(0, 0, 75, 115)  # 左上方的退出按钮

    FIRST_CLICK_EMPTY_RECT: ClassVar[Rect] = Rect(700, 700, 1240, 750)  # 点击空白处关闭

    def __init__(self, ctx: Context, first: bool, timeout_seconds: float):
        """
        需要在忘却之庭关卡内使用
        等待界面加载
        :param ctx: 上下文
        :param first: 是否第一关
        :param timeout_seconds: 等待超时时间
        """
        super().__init__(ctx, op_name=gt('忘却之庭加载关卡', 'ui'), timeout_seconds=timeout_seconds)
        self.first: bool = first

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        part, _ = cv2_utils.crop_image(screen, WaitNodeStart.EXIT_BTN)

        match_result_list = self.ctx.im.match_template(part, 'ui_icon_10', only_best=True)

        if len(match_result_list) > 0:
            if self.first:  # 节点1的时候有一个效果提示 TODO 需要判断最后一关有没有
                click = self.ocr_and_click_one_line('点击空白处关闭', WaitNodeStart.FIRST_CLICK_EMPTY_RECT)
                if click == Operation.OCR_CLICK_SUCCESS:
                    return Operation.round_success()
                else:
                    time.sleep(0.5)
                    return Operation.round_wait('click_empty_fail')
            else:
                return Operation.round_success()
        else:
            time.sleep(0.5)
            return Operation.round_wait()

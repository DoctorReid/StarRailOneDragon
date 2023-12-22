import time
from typing import Union, ClassVar

from basic import Point, Rect, str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.context import Context
from sr.operation import Operation, OperationOneRoundResult


class TakePhoto(Operation):

    TAKE_BTN: ClassVar[Point] = Point(1761, 537)  # 拍照按钮
    SAVE_BTN: ClassVar[Rect] = Rect(1415, 955, 1488, 988)  # 拍照后【保存】按钮的位置

    def __init__(self, ctx: Context):
        """
        需要已经打开拍照框后使用
        点击右方按钮进行拍照 出现保存框后完成
        :param ctx:
        """
        super().__init__(ctx, op_name=gt('拍照', 'ui'), try_times=10)

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        part, _ = cv2_utils.crop_image(screen, TakePhoto.SAVE_BTN)
        ocr_str = self.ctx.ocr.ocr_for_single_line(part)

        if str_utils.find_by_lcs(gt('保存', 'ocr'), ocr_str, percent=0.1):
            return Operation.round_success()

        # 还没有保存按钮 尝试点击拍照
        self.ctx.controller.click(TakePhoto.TAKE_BTN)
        return Operation.round_retry(wait=1)

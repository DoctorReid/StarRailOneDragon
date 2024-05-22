import time
from typing import Optional

from basic import Rect
from basic.i18_utils import gt
from sr.context import Context
from sr.operation import Operation, OperationOneRoundResult


class OcrClickOneLine(Operation):

    def __init__(self, ctx: Context, rect: Rect, target_cn: str,
                 lcs_percent: float = 0.1,
                 wait_after_success: Optional[float] = None):
        """
        OCR识别单行文字 并进行点击
        :param ctx: 上下文
        :param rect: 目标区域
        :param target_cn: 目标文本
        :param lcs_percent: OCR匹配时LCS阈值
        :param wait_after_success: 点击成功后等待秒数
        """
        super().__init__(ctx, try_times=5,
                         op_name='%s %s' % (gt('识别单行文本并点击', 'ui'), gt(target_cn, 'ui')))
        self.rect: Rect = rect
        self.target_cn: str = target_cn
        self.lcs_percent: float = lcs_percent
        self.wait_after_success: Optional[float] = wait_after_success

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        click = self.ocr_and_click_one_line(self.target_cn, self.rect, screen,
                                            lcs_percent=self.lcs_percent,
                                            wait_after_success=self.wait_after_success)

        if click == Operation.OCR_CLICK_SUCCESS:
            return self.round_success()
        elif click == Operation.OCR_CLICK_FAIL:
            time.sleep(1)
            return self.round_retry('点击失败')
        elif click == Operation.OCR_CLICK_NOT_FOUND:
            time.sleep(1)
            return self.round_retry('识别不到文本')

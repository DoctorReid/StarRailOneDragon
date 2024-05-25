from typing import Optional, ClassVar, Union

from basic import Point, Rect
from basic.i18_utils import gt
from sr.context import Context
from sr.operation import Operation, OperationOneRoundResult


class ClickPoint(Operation):

    def __init__(self, ctx: Context, point: Point,
                 try_times: int = 3,
                 click_name_cn: Optional[str] = None,
                 wait_retry: Optional[float] = None):
        """
        点击指定坐标
        :param ctx: 上下文
        :param point: 坐标
        :param try_times: 尝试点击次数
        :param click_name_cn: 点击内容的
        :param wait_retry: 重试前等待的秒数
        """
        super().__init__(
            ctx,
            op_name='%s %s' % (
                gt('点击', 'ui'),
                point if click_name_cn is None else gt(click_name_cn, 'ui')
            ),
            try_times=try_times
        )
        self.point: Point = point

    def _execute_one_round(self) -> OperationOneRoundResult:
        before_error = self.before_click_check_err()
        if before_error is not None:
            return self.round_retry(before_error)

        if not self.ctx.controller.click(self.point):
            return self.round_retry('点击失败')

        after_error = self.after_click_check_err()
        if after_error is not None:
            return self.round_retry(after_error)
        else:
            return self.round_success()

    def before_click_check_err(self) -> Optional[str]:
        """
        点击前检测 是否不符合点击条件
        只有符合条件才会进行点击
        :return: 不符合点击条件的原因
        """
        return None

    def after_click_check_err(self) -> Optional[str]:
        """
        点击后检测 是否符合点击后的现象
        只有符合点击后的现象 指令才会返回成功
        :return: 不符合点击后现象的原因
        """
        return None


class ClickDialogConfirm(Operation):

    CONFIRM_BTN: ClassVar[Rect] = Rect(1024, 647, 1329, 698)  # 确认

    def __init__(self, ctx: Context,
                 wait_after_success: Optional[int] = None):
        """
        点击对话框的确认 当前使用情况有
        - 模拟宇宙 丢弃奇物
        - 模拟宇宙 丢弃祝福
        :param ctx:
        :param wait_after_success: 点击成功后等待的秒数
        """
        super().__init__(ctx, op_name=gt('点击确认', 'ui'))
        self.wait_after_success: Optional[int] = wait_after_success

    def _execute_one_round(self) -> OperationOneRoundResult:
        click = self.ocr_and_click_one_line('确认', ClickDialogConfirm.CONFIRM_BTN)
        if click == Operation.OCR_CLICK_SUCCESS:
            return self.round_success(wait=self.wait_after_success)
        else:
            return self.round_retry('点击确认失败', wait=1)

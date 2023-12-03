import time

from cv2.typing import MatLike

from basic.i18_utils import gt
from sr.context import Context
from sr.image.sceenshot import secondary_ui
from sr.operation import Operation, OperationOneRoundResult


class WaitInHall(Operation):

    def __init__(self, ctx: Context):
        """
        等待页面加载完成 左上角出现【忘却之庭】
        目前有以下情况
        - 指南中【传送】 或者 使者中进入
        - 战斗结束后【返回忘却之庭】
        :param ctx:
        """
        super().__init__(ctx, try_times=30, op_name=gt('忘却之庭 等待加载主页', 'ui'))

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen: MatLike = self.screenshot()

        if not secondary_ui.in_secondary_ui(screen, self.ctx.ocr, secondary_ui.TITLE_FORGOTTEN_HALL.cn):
            time.sleep(1)
            return Operation.round_retry()
        else:
            return Operation.round_success()

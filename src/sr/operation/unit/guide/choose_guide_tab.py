import time

from cv2.typing import MatLike

from basic.i18_utils import gt
from sr.context import Context
from sr.image.sceenshot import secondary_ui
from sr.operation import Operation, OperationOneRoundResult
from sr.operation.unit.guide import GuideTab


class ChooseGuideTab(Operation):
    """
    使用前需要已经打开【星际和平指南】

    选择对应的TAB
    """
    def __init__(self, ctx: Context, target: GuideTab):
        super().__init__(ctx, try_times=5,
                         op_name=gt('打开指南', 'ui') + ' ' + gt(target.cn, 'ui'))

        self.target: GuideTab = target

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen: MatLike = self.screenshot()

        if not secondary_ui.in_secondary_ui(screen, self.ctx.ocr, secondary_ui.TITLE_GUIDE.cn):
            return Operation.round_retry()

        if not secondary_ui.in_secondary_ui(screen, self.ctx.ocr, self.target.cn):
            self.ctx.controller.click(self.target.rect.center)
            time.sleep(1)
            return Operation.round_retry()

        return Operation.round_success()

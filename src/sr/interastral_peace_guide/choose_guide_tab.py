import time

from cv2.typing import MatLike

from basic.i18_utils import gt
from basic.log_utils import log
from sr.context import Context
from sr.image.sceenshot.screen_state import in_secondary_ui
from sr.image.sceenshot.screen_state_enum import ScreenState
from sr.operation import Operation, OperationOneRoundResult
from sr.interastral_peace_guide.guide_const import GuideTab


class ChooseGuideTab(Operation):

    def __init__(self, ctx: Context, target: GuideTab):
        """
        使用前需要已经打开【星际和平指南】

        选择对应的TAB
        """
        super().__init__(ctx, try_times=5,
                         op_name=gt('打开指南', 'ui') + ' ' + gt(target.cn, 'ui'),
                         )

        self.target: GuideTab = target
        """需要选择的分类"""

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen: MatLike = self.screenshot()

        if not in_secondary_ui(screen, self.ctx.ocr, ScreenState.GUIDE.value):
            log.info('等待指南加载')
            return self.round_retry()

        if not in_secondary_ui(screen, self.ctx.ocr, self.target.cn):
            log.info('指南中点击 %s', self.target.cn)
            self.ctx.controller.click(self.target.area.rect.center)
            time.sleep(1)
            return self.round_retry()

        return self.round_success()

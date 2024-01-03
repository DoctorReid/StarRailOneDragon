from typing import ClassVar

from cv2.typing import MatLike

from basic import Rect
from basic.i18_utils import gt
from sr.context import Context
from sr.image.sceenshot.screen_state import in_secondary_ui, ScreenState
from sr.operation import Operation, OperationOneRoundResult


class StartSimUni(Operation):

    STATUS_RESTART: ClassVar[str] = '开始'
    STATUS_CONTINUE: ClassVar[str] = '继续'

    RESTART_BTN: ClassVar[Rect] = Rect(1418, 970, 1656, 997)  # 下载初始角色
    CONTINUE_BTN: ClassVar[Rect] = Rect(0, 0, 0, 0)  # 继续

    def __init__(self, ctx: Context):
        """
        需要在模拟宇宙入口页面中使用 且先选择了普通模拟宇宙
        选择 开始挑战 或 继续
        :param ctx:
        """
        super().__init__(ctx, try_times=5,
                         op_name='%s %s' % (gt('模拟宇宙', 'ui'), gt('开始挑战', 'ui')))

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen: MatLike = self.screenshot()

        if not in_secondary_ui(screen, self.ctx.ocr, ScreenState.SIM_TYPE_NORMAL.value):
            return Operation.round_retry('未在模拟宇宙页面', wait=1)

        click = self.ocr_and_click_one_line('重新开始', StartSimUni.RESTART_BTN, screen=screen)

        if click == Operation.OCR_CLICK_SUCCESS:
            return Operation.round_success(status=StartSimUni.STATUS_RESTART)

        click = self.ocr_and_click_one_line('继续', StartSimUni.CONTINUE_BTN, screen=screen)

        if click == Operation.OCR_CLICK_SUCCESS:
            return Operation.round_success(status=StartSimUni.STATUS_CONTINUE)

        return Operation.round_retry('点击开始失败', wait=1)

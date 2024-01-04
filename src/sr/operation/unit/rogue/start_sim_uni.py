from typing import ClassVar, List

from cv2.typing import MatLike

from basic import Rect
from basic.i18_utils import gt
from sr.context import Context
from sr.image.sceenshot.screen_state import in_secondary_ui, ScreenState
from sr.operation import Operation, OperationOneRoundResult, StateOperation, StateOperationNode, StateOperationEdge


class StartSimUni(StateOperation):

    STATUS_RESTART: ClassVar[str] = '开始'
    STATUS_CONTINUE: ClassVar[str] = '继续'

    RESTART_BTN: ClassVar[Rect] = Rect(1418, 970, 1656, 997)  # 下载初始角色
    CONFIRM_BTN: ClassVar[Rect] = Rect(1519, 963, 1721, 1002)  # 启动模拟宇宙
    CONTINUE_BTN: ClassVar[Rect] = Rect(1573, 968, 1728, 997)  # 继续进度
    END_BTN: ClassVar[Rect] = Rect(1202, 965, 1350, 1000)  # 结束并结算

    def __init__(self, ctx: Context):
        """
        需要在模拟宇宙入口页面中使用 且先选择了普通模拟宇宙
        选择 重新开始 或 继续
        :param ctx:
        """
        edges: List[StateOperationEdge] = []

        start = StateOperationNode('开始', self._restart_or_continue)
        confirm = StateOperationNode('启动', self._confirm_start)
        edges.append(StateOperationEdge(start, confirm, status=StartSimUni.STATUS_RESTART))

        super().__init__(ctx,
                         try_times=5,
                         op_name='%s %s' % (gt('模拟宇宙', 'ui'), gt('开始挑战', 'ui')),
                         edges=edges
                         )

    def _restart_or_continue(self) -> OperationOneRoundResult:
        screen: MatLike = self.screenshot()

        if not in_secondary_ui(screen, self.ctx.ocr, ScreenState.SIM_TYPE_NORMAL.value):
            return Operation.round_retry('未在模拟宇宙页面', wait=1)

        click = self.ocr_and_click_one_line('重新开始', StartSimUni.RESTART_BTN, screen=screen)

        if click == Operation.OCR_CLICK_SUCCESS:
            return Operation.round_success(status=StartSimUni.STATUS_RESTART, wait=2)

        click = self.ocr_and_click_one_line('继续', StartSimUni.CONTINUE_BTN, screen=screen)

        if click == Operation.OCR_CLICK_SUCCESS:
            return Operation.round_success(status=StartSimUni.STATUS_CONTINUE, wait=2)

        return Operation.round_retry('点击开始失败', wait=1)

    def _confirm_start(self) -> OperationOneRoundResult:
        screen: MatLike = self.screenshot()

        click = self.ocr_and_click_one_line('启动模拟宇宙', StartSimUni.CONFIRM_BTN, screen=screen)

        if click == Operation.OCR_CLICK_SUCCESS:
            return Operation.round_success(status=StartSimUni.STATUS_RESTART, wait=2)

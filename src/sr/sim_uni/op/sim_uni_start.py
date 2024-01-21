from typing import ClassVar, List

from cv2.typing import MatLike

from basic import Rect, str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.context import Context
from sr.image.sceenshot import screen_state
from sr.image.sceenshot.screen_state import in_secondary_ui, ScreenState
from sr.operation import Operation, OperationOneRoundResult, StateOperation, StateOperationNode, StateOperationEdge


class SimUniStart(StateOperation):

    STATUS_RESTART: ClassVar[str] = '重新开始'
    STATUS_CONTINUE: ClassVar[str] = '继续'

    RESTART_BTN: ClassVar[Rect] = Rect(1418, 970, 1656, 997)  # 下载初始角色
    START_BTN: ClassVar[Rect] = Rect(1519, 963, 1721, 1002)  # 启动模拟宇宙
    CONTINUE_BTN: ClassVar[Rect] = Rect(1573, 968, 1728, 997)  # 继续进度
    CONFIRM_BTN: ClassVar[Rect] = Rect(1005, 647, 1337, 696)  # 低等级确认
    END_BTN: ClassVar[Rect] = Rect(1202, 965, 1350, 1000)  # 结束并结算

    def __init__(self, ctx: Context):
        """
        需要在模拟宇宙入口页面中使用 且先选择了普通模拟宇宙
        选择 重新开始 或 继续
        :param ctx:
        """
        edges: List[StateOperationEdge] = []

        restart_or_continue = StateOperationNode('开始', self._restart_or_continue)
        start = StateOperationNode('启动', self._start)
        edges.append(StateOperationEdge(restart_or_continue, start, status=SimUniStart.STATUS_RESTART))

        confirm = StateOperationNode('确认', self._confirm)
        edges.append(StateOperationEdge(start, confirm, status=SimUniStart.STATUS_RESTART))

        super().__init__(ctx,
                         try_times=5,
                         op_name='%s %s' % (gt('模拟宇宙', 'ui'), gt('开始挑战', 'ui')),
                         edges=edges
                         )

    def _restart_or_continue(self) -> OperationOneRoundResult:
        screen: MatLike = self.screenshot()

        if not in_secondary_ui(screen, self.ctx.ocr, ScreenState.SIM_TYPE_NORMAL.value):
            return Operation.round_retry('未在模拟宇宙页面', wait=1)

        click = self.ocr_and_click_one_line('重新开始', SimUniStart.RESTART_BTN, screen=screen)

        if click == Operation.OCR_CLICK_SUCCESS:
            return Operation.round_success(status=SimUniStart.STATUS_RESTART, wait=2)

        click = self.ocr_and_click_one_line('继续', SimUniStart.CONTINUE_BTN, screen=screen)

        if click == Operation.OCR_CLICK_SUCCESS:
            return Operation.round_success(status=SimUniStart.STATUS_CONTINUE, wait=2)

        return Operation.round_retry('点击开始失败', wait=1)

    def _start(self) -> OperationOneRoundResult:
        """
        启动模拟宇宙
        :return:
        """
        screen: MatLike = self.screenshot()

        click = self.ocr_and_click_one_line('启动模拟宇宙', SimUniStart.START_BTN, screen=screen)

        if click == Operation.OCR_CLICK_SUCCESS:
            return Operation.round_success(status=SimUniStart.STATUS_RESTART, wait=2)
        else:
            return Operation.round_retry('点击启动模拟宇宙失败')

    def _confirm(self) -> OperationOneRoundResult:
        """
        低等级确认
        :return:
        """
        screen: MatLike = self.screenshot()

        if screen_state.in_sim_uni_choose_path(screen, self.ctx.ocr):
            return Operation.round_success(status=SimUniStart.STATUS_RESTART)

        click = self.ocr_and_click_one_line('确认', SimUniStart.CONFIRM_BTN, screen=screen)

        if click == Operation.OCR_CLICK_SUCCESS:
            return Operation.round_success(status=SimUniStart.STATUS_RESTART, wait=2)
        else:
            return Operation.round_retry('点击确认失败')

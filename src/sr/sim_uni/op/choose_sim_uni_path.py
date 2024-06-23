from typing import List, Optional, ClassVar

from cv2.typing import MatLike

from basic import Point, Rect
from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.const import STANDARD_CENTER_POS
from sr.context.context import Context
from sr.image.sceenshot.screen_state import in_secondary_ui
from sr.image.sceenshot.screen_state_enum import ScreenState
from sr.operation import StateOperation, StateOperationNode, OperationOneRoundResult, Operation
from sr.sim_uni.sim_uni_const import SimUniPath


class ChooseSimUniPath(StateOperation):

    PATH_RECT: ClassVar[Rect] = Rect(134, 665, 1788, 708)  # 命途
    CONFIRM_BTN: ClassVar[Rect] = Rect(1529, 957, 1869, 1006)  # 确认命途

    def __init__(self, ctx: Context, path: SimUniPath):
        """
        需要在模拟宇宙-选择命途页面中使用
        选择对应的命途
        :param ctx:
        :param path: 目标命途
        """
        nodes: List[StateOperationNode] = [
            StateOperationNode('选择命途', self._choose_target_path),
            StateOperationNode('确认命途', self._confirm_path)
        ]

        super().__init__(ctx, try_times=5,
                         op_name='%s %s' % (gt('模拟宇宙', 'ui'), gt('选择命途', 'ui')),
                         nodes=nodes
                         )
        self.path: SimUniPath = path

    def _choose_target_path(self) -> OperationOneRoundResult:
        """
        选择命途
        :return:
        """
        screen = self.screenshot()

        if not in_secondary_ui(screen, self.ctx.ocr, ScreenState.SIM_PATH.value):
            return self.round_retry('未在模拟宇宙命途页面', wait=1)

        target_pos = self._get_target_path_pos(screen)

        if target_pos is None:  # 找不到的时候往右滑一下
            drag_from = STANDARD_CENTER_POS
            drag_to = drag_from + Point(-200, 0)
            self.ctx.controller.drag_to(end=drag_to, start=drag_from)
            return self.round_retry('未找到目标命途', wait=1)

        self.ctx.controller.click(target_pos)
        return self.round_success(wait=1)

    def _get_target_path_pos(self, screen: Optional[MatLike] = None) -> Optional[Point]:
        """
        获取对应命途所在的位置
        :param screen: 屏幕截图
        :return:
        """
        if screen is None:
            screen = self.screenshot()

        part, _ = cv2_utils.crop_image(screen, ChooseSimUniPath.PATH_RECT)

        mr = self.ctx.ocr.match_one_best_word(part, word=self.path.value, lcs_percent=0.1)

        if mr is None:
            return None
        else:
            return mr.center + ChooseSimUniPath.PATH_RECT.left_top

    def _confirm_path(self) -> OperationOneRoundResult:
        """
        确认命途
        :return:
        """
        click = self.ocr_and_click_one_line('确认命途', ChooseSimUniPath.CONFIRM_BTN,
                                            lcs_percent=0.1)
        if click == Operation.OCR_CLICK_SUCCESS:
            return self.round_success(wait=2)
        else:
            return self.round_retry('点击确认命途失败')

import time
from typing import Optional, ClassVar

from cv2.typing import MatLike

from basic import Rect, str_utils, Point
from basic.i18_utils import gt
from basic.img import cv2_utils, MatchResult
from basic.log_utils import log
from sr.context import Context
from sr.operation import Operation, OperationOneRoundResult


class ChooseSupport(Operation):

    SUPPORT_BTN_RECT: ClassVar[Rect] = Rect(1670, 690, 1830, 770)  # 【支援】按钮
    CHARACTER_LIST_RECT: ClassVar[Rect] = Rect(70, 160, 520, 940)  # 支援角色列表
    JOIN_BTN_RECT: ClassVar[Rect] = Rect(1560, 970, 1840, 1010)  # 【入队】按钮

    STATUS_SUPPORT_NOT_FOUND: ClassVar[str] = 'support_not_found'

    def __init__(self, ctx: Context, character_id: Optional[str]):
        """
        需要在管理配队页面使用 选择对应支援角色
        如果不传入支援角色 则直接返回成功
        :param ctx:
        :param character_id:
        """
        super().__init__(ctx, try_times=3, op_name=gt('选择支援', 'ui'))
        self.phase: int = 0
        self.character_id: Optional[str] = character_id
        self.no_find_character_times: int = 0

    def _execute_one_round(self) -> OperationOneRoundResult:
        if self.character_id is None:
            return Operation.round_success()

        if self.phase == 0:  # 点击【支援】按钮
            click = self.ocr_and_click_one_line(self.screenshot(), '支援', ChooseSupport.SUPPORT_BTN_RECT,
                                                wait_after_success=1.5)
            if click == Operation.OCR_CLICK_SUCCESS:
                self.phase += 1
                return Operation.round_wait()
            else:
                return Operation.round_retry()
        elif self.phase == 1:  # 选择角色
            click = self._find_and_click_character()
            if click:
                self.phase += 1
                return Operation.round_wait()
            else:
                self.no_find_character_times += 1
                if self.no_find_character_times >= 5:
                    # 找不到支援角色 点击右边返回 按特殊状态返回成功
                    self.ctx.controller.click(ChooseSupport.SUPPORT_BTN_RECT.center)
                    time.sleep(1.5)
                    return Operation.round_success(ChooseSupport.STATUS_SUPPORT_NOT_FOUND)
                return Operation.round_wait()
        elif self.phase == 2:  # 点击【入队】按钮
            click = self.ocr_and_click_one_line(self.screenshot(), '入队', ChooseSupport.JOIN_BTN_RECT,
                                                wait_after_success=1.5)
            if click == Operation.OCR_CLICK_SUCCESS:
                return Operation.round_success()
            else:
                return Operation.round_retry()

        return Operation.round_fail('unknown_phase')

    def _find_and_click_character(self) -> bool:
        """
        找到目标角色并点击
        :return:
        """
        pos = self._find_character()
        if pos is None:
            drag_from = ChooseSupport.CHARACTER_LIST_RECT.center
            drag_to = drag_from + Point(0, -200)
            self.ctx.controller.drag_to(drag_to, drag_from)
            time.sleep(1)
            return False
        else:
            return self.ctx.controller.click(pos.center)


    def _find_character(self) -> Optional[MatchResult]:
        """
        找到角色头像的位置
        :return:
        """
        screen: MatLike = self.screenshot()
        part, _ = cv2_utils.crop_image(screen, ChooseSupport.CHARACTER_LIST_RECT)

        source_kps, source_desc = cv2_utils.feature_detect_and_compute(part)
        template = self.ctx.ih.get_character_avatar_template(self.character_id)
        if template is None:
            log.error('找不到角色头像模板 %s', self.character_id)
            return None

        pos = cv2_utils.feature_match_for_one(
            source_kps, source_desc,
            template.kps, template.desc,
            template.origin.shape[1], template.origin.shape[0])

        if pos is not None:
            lt = ChooseSupport.CHARACTER_LIST_RECT.left_top
            pos.x += lt.x
            pos.y += lt.y

        return pos

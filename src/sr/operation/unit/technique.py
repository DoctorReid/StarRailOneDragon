from typing import ClassVar, List

from cv2.typing import MatLike

from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.context import Context
from sr.image.ocr_matcher import OcrMatcher
from sr.image.sceenshot import screen_state
from sr.operation import Operation, OperationOneRoundResult, StateOperation, StateOperationEdge, StateOperationNode
from sr.screen_area.dialog import ScreenDialog
from sr.screen_area.screen_normal_world import ScreenNormalWorld


def pc_can_use_technique(screen: MatLike, ocr: OcrMatcher, key: str) -> bool:
    """
    PC端使用 判断当前是否可以使用秘技 - 秘技按钮上有显示快捷键
    :param screen: 屏幕棘突
    :param ocr: OCR
    :param key: 秘技按键
    :return:
    """
    area = ScreenNormalWorld.TECH_KEY.value
    part = cv2_utils.crop_image_only(screen, area.rect)
    # cv2_utils.show_image(part, win_name='pc_can_use_technique', wait=0)
    ocr_result = ocr.ocr_for_single_line(part)

    if ocr_result is not None and ocr_result.lower() == key.lower():
        return True
    else:
        return False


class UseTechnique(StateOperation):

    STATUS_NO_NEED_CONSUMABLE: ClassVar[str] = '无需使用消耗品'
    STATUS_NO_USE_CONSUMABLE: ClassVar[str] = '没使用消耗品'
    STATUS_USE_CONSUMABLE: ClassVar[str] = '使用了消耗品'

    def __init__(self, ctx: Context,
                 use_consumable: int = 0):
        """
        需在大世界页面中使用
        用当前角色使用秘技
        返回 data=是否使用了秘技
        :param ctx:
        :param use_consumable: 秘技点不足时是否可以使用消耗品 0=不可以 1=使用1个 2=连续使用至满
        """
        edges: List[StateOperationEdge] = []

        use = StateOperationNode('使用秘技', self._use)
        confirm = StateOperationNode('确认', self._confirm)
        edges.append(StateOperationEdge(use, confirm))
        edges.append(StateOperationEdge(confirm, use, status=UseTechnique.STATUS_USE_CONSUMABLE))

        super().__init__(ctx, try_times=5,
                         op_name=gt('施放秘技', 'ui'),
                         edges=edges,
                         specified_start_node=use)

        self.use_consumable: int = use_consumable  # 是否可以使用消耗品
        self.use_consumable_times: int = 0  # 使用消耗品的次数
        self.use_technique: bool = False  # 是否使用了秘技

    def _init_before_execute(self):
        self.use_consumable_times: int = 0  # 使用消耗品的次数
        self.use_technique: bool = False  # 是否使用了秘技

    def _use(self) -> OperationOneRoundResult:
        self.ctx.controller.use_technique()
        self.use_technique = True
        return Operation.round_success(wait=0.5)

    def _confirm(self) -> OperationOneRoundResult:
        """
        使用消耗品确认
        :return:
        """
        screen = self.screenshot()
        if screen_state.is_normal_in_world(screen, self.ctx.im):  # 无需使用
            return Operation.round_success(UseTechnique.STATUS_NO_NEED_CONSUMABLE, data=self.use_technique)

        area = ScreenDialog.FAST_RECOVER_TITLE.value
        if not self.find_area(area, screen):  # 没有出现对话框的话 认为进入了战斗
            return Operation.round_success(UseTechnique.STATUS_NO_NEED_CONSUMABLE, data=self.use_technique)

        self.use_technique = False

        if self.use_consumable == 0:  # 不可以使用消耗品
            area = ScreenDialog.FAST_RECOVER_CANCEL.value
            click = self.find_and_click_area(area, screen)
            if click == Operation.OCR_CLICK_SUCCESS:
                return Operation.round_success(UseTechnique.STATUS_NO_USE_CONSUMABLE, wait=0.5, data=self.use_technique)
            else:
                return Operation.round_retry('点击%s失败' % area.status, wait=1)
        elif self.find_area(ScreenDialog.FAST_RECOVER_NO_CONSUMABLE.value, screen):  # 没有消耗品可以使用
            area = ScreenDialog.FAST_RECOVER_CANCEL.value
            click = self.find_and_click_area(area, screen)
            if click == Operation.OCR_CLICK_SUCCESS:
                if self.use_consumable_times > 0:
                    return Operation.round_success(UseTechnique.STATUS_USE_CONSUMABLE, wait=0.5, data=self.use_technique)
                else:
                    return Operation.round_success(UseTechnique.STATUS_NO_USE_CONSUMABLE, wait=0.5, data=self.use_technique)
            else:
                return Operation.round_retry('点击%s失败' % area.status, wait=1)
        elif self.use_consumable == 1 and self.use_consumable_times >= 1:  # 只能用1次 而已经用了
            area = ScreenDialog.FAST_RECOVER_CANCEL.value
            click = self.find_and_click_area(area, screen)
            if click == Operation.OCR_CLICK_SUCCESS:
                return Operation.round_success(UseTechnique.STATUS_USE_CONSUMABLE, wait=0.5, data=self.use_technique)
            else:
                return Operation.round_retry('点击%s失败' % area.status, wait=1)
        else:  # 还需要使用消耗品
            area = ScreenDialog.FAST_RECOVER_CONFIRM.value
            click = self.find_and_click_area(area, screen)
            if click == Operation.OCR_CLICK_SUCCESS:
                self.use_consumable_times += 1
                return Operation.round_success(UseTechnique.STATUS_USE_CONSUMABLE, wait=0.5, data=self.use_technique)
            elif click == Operation.OCR_CLICK_NOT_FOUND:  # 使用满了
                area = ScreenDialog.FAST_RECOVER_CANCEL.value
                click = self.find_and_click_area(area, screen)
                if click == Operation.OCR_CLICK_SUCCESS:
                    if self.use_consumable_times > 0:
                        return Operation.round_success(UseTechnique.STATUS_USE_CONSUMABLE, wait=0.5, data=self.use_technique)
                    else:
                        return Operation.round_success(UseTechnique.STATUS_NO_USE_CONSUMABLE, wait=0.5, data=self.use_technique)
                else:
                    return Operation.round_retry('点击%s失败' % area.status, wait=1)
            else:
                return Operation.round_retry('点击%s失败' % area.status, wait=1)

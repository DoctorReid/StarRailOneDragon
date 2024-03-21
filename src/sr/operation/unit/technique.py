import time
from typing import ClassVar, List, Optional

from cv2.typing import MatLike

from basic import str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.context import Context
from sr.image.ocr_matcher import OcrMatcher
from sr.image.sceenshot import screen_state, battle
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


def get_technique_point(screen: MatLike,
                        ocr: OcrMatcher) -> Optional[int]:
    rect_list = [
        ScreenNormalWorld.TECHNIQUE_POINT_1.value.rect,
        ScreenNormalWorld.TECHNIQUE_POINT_2.value.rect,
    ]
    for rect in rect_list:
        part = cv2_utils.crop_image_only(screen, rect)

        ocr_result = ocr.ocr_for_single_line(part, strict_one_line=True)
        point = str_utils.get_positive_digits(ocr_result, None)
        if point is not None:
            return point

    return None


class UseTechnique(StateOperation):

    STATUS_CAN_USE: ClassVar[str] = '可使用秘技'
    STATUS_NO_NEED_CONSUMABLE: ClassVar[str] = '无需使用消耗品'
    STATUS_NO_USE_CONSUMABLE: ClassVar[str] = '没使用消耗品'
    STATUS_USE_CONSUMABLE: ClassVar[str] = '使用了消耗品'

    def __init__(self, ctx: Context,
                 use_consumable: int = 0,
                 need_check_available: bool = False,
                 need_check_point: bool = False
                 ):
        """
        需在大世界页面中使用
        用当前角色使用秘技
        返回 data=是否使用了秘技
        :param ctx:
        :param use_consumable: 秘技点不足时是否可以使用消耗品 0=不可以 1=使用1个 2=连续使用至满
        :param need_check_available: 是否需要检查秘技是否可用 普通大世界战斗后 会有一段时间才能使用秘技
        :param need_check_point: 是否检测剩余秘技点再使用。如果没有秘技点 又不能用消耗品 那就不使用了
        """
        edges: List[StateOperationEdge] = []

        check = StateOperationNode('检测秘技点', self._check_technique_point)

        use = StateOperationNode('使用秘技', self._use)
        edges.append(StateOperationEdge(check, use, status=UseTechnique.STATUS_CAN_USE))

        confirm = StateOperationNode('确认', self._confirm)
        edges.append(StateOperationEdge(use, confirm))
        edges.append(StateOperationEdge(confirm, use, status=UseTechnique.STATUS_USE_CONSUMABLE))

        super().__init__(ctx, try_times=10,
                         op_name=gt('施放秘技', 'ui'),
                         edges=edges,
                         specified_start_node=check)

        self.use_consumable: int = use_consumable  # 是否可以使用消耗品
        self.use_consumable_times: int = 0  # 使用消耗品的次数
        self.use_technique: bool = False  # 是否使用了秘技
        self.need_check_available: bool = need_check_available  # 是否需要检查秘技是否可用
        self.need_check_point: bool = need_check_point

    def _init_before_execute(self):
        super()._init_before_execute()
        self.use_consumable_times: int = 0  # 使用消耗品的次数
        self.use_technique: bool = False  # 是否使用了秘技

    def _check_technique_point(self) -> OperationOneRoundResult:
        if self.need_check_point:
            screen = self.screenshot()
            point = get_technique_point(screen, self.ctx.ocr)
            if point > 0:  # 有秘技点 随便用
                return Operation.round_success(UseTechnique.STATUS_CAN_USE)
            elif self.use_consumable == 0 or self.ctx.no_technique_recover_consumables:  # 没有秘技点又不能用药或者没有药 就不要用了
                return Operation.round_success()
            else:  # 没有秘技点 可能有药 尝试
                return Operation.round_success(UseTechnique.STATUS_CAN_USE)
        else:
            return Operation.round_success(UseTechnique.STATUS_CAN_USE)

    def _use(self) -> OperationOneRoundResult:
        if self.need_check_available:
            screen = self.screenshot()
            if not pc_can_use_technique(screen, self.ctx.ocr, self.ctx.game_config.key_technique):
                return Operation.round_retry(wait=0.25)

        self.ctx.controller.use_technique()
        self.ctx.controller.stop_moving_forward()  # 在使用秘技中停止移动 可以取消停止移动的后摇
        self.use_technique = True  # 与context的状态分开 ctx的只负责记录开怪位 后续考虑变量改名
        self.ctx.technique_used = True
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
        self.ctx.technique_used = False

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
                self.ctx.no_technique_recover_consumables = True  # 设置没有药可以用了
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


class CheckTechniquePoint(Operation):

    def __init__(self, ctx: Context):
        """
        需在大世界页面中使用
        通过右下角数字 检测当前剩余的秘技点数
        返回附加状态为秘技点数
        :param ctx:
        """
        super().__init__(ctx, try_times=5, op_name=gt('检测秘技点数', 'ui'))

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()
        if battle.IN_WORLD != battle.get_battle_status(screen, self.ctx.im):
            time.sleep(1)
            return Operation.round_retry('未在大世界界面')

        digit = get_technique_point(screen, self.ctx.ocr)

        if digit is None:
            return Operation.round_retry('未检测到数字', wait=0.5)

        return Operation.round_success(status=str(digit), data=digit)

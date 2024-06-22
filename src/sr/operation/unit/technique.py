import time
from typing import ClassVar, List, Optional

from cv2.typing import MatLike

from basic import str_utils
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


class UseTechniqueResult:

    def __init__(self, use_tech: bool = False, with_dialog: bool = False,
                 use_consumable_times: int = 0,
                 consumable_chosen: bool = False):

        self.use_tech: bool = use_tech
        """是否使用了秘技"""

        self.with_dialog: bool = with_dialog
        """是否出现了消耗品对话框"""

        self.use_consumable_times: int = use_consumable_times
        """使用消耗品的数量"""

        self.consumable_chosen: bool = consumable_chosen
        """是否已经选择了消耗品"""


class UseTechnique(StateOperation):

    STATUS_CAN_USE: ClassVar[str] = '可使用秘技'

    def __init__(self, ctx: Context,
                 max_consumable_cnt: int = 0,
                 need_check_available: bool = False,
                 need_check_point: bool = False,
                 quirky_snacks: bool = False
                 ):
        """
        需在大世界页面中使用
        用当前角色使用秘技
        返回 data=UseTechniqueResult
        这个方法有用在了开怪上 因此判断需要快点 防止被袭
        :param ctx:
        :param max_consumable_cnt: 秘技点不足时最多使用的消耗品个数
        :param need_check_available: 是否需要检查秘技是否可用 普通大世界战斗后 会有一段时间才能使用秘技
        :param need_check_point: 是否检测剩余秘技点再使用。如果没有秘技点 又不能用消耗品 那就不使用了。目前OCR较慢 不建议开启
        :param quirky_snacks: 只使用奇巧零食
        """
        edges: List[StateOperationEdge] = []

        check = StateOperationNode('检测秘技点', self._check_technique_point)

        use = StateOperationNode('使用秘技', self._use)
        edges.append(StateOperationEdge(check, use, status=UseTechnique.STATUS_CAN_USE))

        confirm = StateOperationNode('确认', self._confirm)
        edges.append(StateOperationEdge(use, confirm))

        # 有使用消耗品 关闭对话框后判断是否在大世界
        wait_for_use = StateOperationNode('等待大世界使用秘技', self._wait_in_world)
        edges.append(StateOperationEdge(confirm, wait_for_use, status=FastRecover.STATUS_USE_CONSUMABLE))
        edges.append(StateOperationEdge(wait_for_use, use))

        # 没有使用消耗品 关闭对话框后判断是否在大世界
        wait_for_other = StateOperationNode('等待大世界继续其它指令', self._wait_in_world)
        edges.append(StateOperationEdge(confirm, wait_for_other, status=FastRecover.STATUS_NO_USE_CONSUMABLE))

        super().__init__(ctx, try_times=20,
                         op_name=gt('施放秘技', 'ui'),
                         edges=edges,
                         specified_start_node=check)

        self.max_consumable_cnt: int = max_consumable_cnt  # 最多使用的消耗品个数
        self.quirky_snacks: bool = quirky_snacks  # 只使用奇巧零食

        self.need_check_available: bool = need_check_available  # 是否需要检查秘技是否可用
        self.need_check_point: bool = need_check_point  # 是否检测剩余秘技点再使用

    def handle_init(self) -> Optional[OperationOneRoundResult]:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        可以返回初始化后判断的结果
        - 成功时跳过本指令
        - 失败时立刻返回失败
        - 不返回时正常运行本指令
        """
        self.op_result: UseTechniqueResult = UseTechniqueResult()  # 最后返回的结果

        return None

    def _check_technique_point(self) -> OperationOneRoundResult:
        if self.need_check_point:
            screen = self.screenshot()
            point = get_technique_point(screen, self.ctx.ocr)
            if point is not None and point > 0:  # 有秘技点 随便用
                return self.round_success(UseTechnique.STATUS_CAN_USE)
            elif self.max_consumable_cnt == 0 or self.ctx.no_technique_recover_consumables:  # 没有秘技点又不能用药或者没有药 就不要用了
                return self.round_success()
            else:  # 没有秘技点 可能有药 尝试
                return self.round_success(UseTechnique.STATUS_CAN_USE)
        else:
            return self.round_success(UseTechnique.STATUS_CAN_USE)

    def _use(self) -> OperationOneRoundResult:
        if self.need_check_available and not self.op_result.with_dialog:
            # 之前出现过消耗品对话框的话 这里就不需要判断了
            screen = self.screenshot()
            if not pc_can_use_technique(screen, self.ctx.ocr, self.ctx.game_config.key_technique):
                return self.round_retry(wait=0.1)

        self.ctx.controller.use_technique()
        self.ctx.controller.stop_moving_forward()  # 在使用秘技中停止移动 可以取消停止移动的后摇
        self.op_result.use_tech = True  # 与context的状态分开 ctx的只负责记录开怪位 后续考虑变量改名
        self.ctx.technique_used = True
        return self.round_success(wait=0.1)

    def _confirm(self) -> OperationOneRoundResult:
        """
        使用消耗品确认
        :return:
        """
        if self.ctx.team_info.is_attack_technique:  # 攻击类的 使用完就取消标记
            self.ctx.technique_used = False

        if self.op_result.with_dialog and self.op_result.use_consumable_times > 0:
            # 之前出现过对话框 且已经用 过消耗品了 那这次就不需要判断了
            return self.round_success(FastRecover.STATUS_NO_NEED_CONSUMABLE, data=self.op_result)

        screen = self.screenshot()
        if screen_state.is_normal_in_world(screen, self.ctx.im):
            # 没有出现消耗品的情况 要尽快返回继续原来的指令 因此不等待
            return self.round_success(FastRecover.STATUS_NO_NEED_CONSUMABLE, data=self.op_result)

        area = ScreenDialog.FAST_RECOVER_TITLE.value
        if not self.find_area(area, screen):  # 没有出现对话框的话 认为进入了战斗
            return self.round_success(FastRecover.STATUS_NO_NEED_CONSUMABLE, data=self.op_result)

        self.op_result.use_tech = False  # 出现了对话框 那么之前使用秘技没有成功
        self.ctx.technique_used = False

        return FastRecover.handle_consumable_dialog(
            self, self.ctx, screen, self.op_result,
            max_consumable_cnt=self.max_consumable_cnt,
            quirky_snacks=self.quirky_snacks
        )

    def _wait_in_world(self):
        """
        使用后判断是否在大世界
        这里需要足够快的判断 方便后续的指令进行 因此尽量等待少的时间
        :return:
        """
        # 没有出现过对话框 那么直接返回即可
        if not self.op_result.with_dialog:
            return self.round_success(data=self.op_result)

        screen = self.screenshot()
        if screen_state.is_normal_in_world(screen, self.ctx.im):
            return self.round_success(data=self.op_result)
        else:
            return self.round_retry(status='未在大世界画面', wait=0.1)


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
        if not screen_state.is_normal_in_world(screen, self.ctx.im):
            time.sleep(1)
            return self.round_retry('未在大世界界面')

        digit = get_technique_point(screen, self.ctx.ocr)

        if digit is None:
            return self.round_retry('未检测到数字', wait=0.5)

        return self.round_success(status=str(digit), data=digit)


class FastRecover(StateOperation):

    STATUS_NO_NEED_CONSUMABLE: ClassVar[str] = '无需使用消耗品'
    STATUS_NO_USE_CONSUMABLE: ClassVar[str] = '没使用消耗品'
    STATUS_USE_CONSUMABLE: ClassVar[str] = '使用了消耗品'

    def __init__(self, ctx: Context,
                 max_consumable_cnt: int = 0,
                 quirky_snacks: bool = False
                 ):
        """
        使用消耗品恢复秘技点
        这个方法有用在了开怪上 因此判断需要快点 防止被袭
        :param ctx:
        :param max_consumable_cnt: 秘技点不足时最多使用的消耗品个数
        :param quirky_snacks: 只使用奇巧零食
        """
        edges: List[StateOperationEdge] = []

        use = StateOperationNode('使用消耗品', self._use)

        # 关闭对话框后判断是否在大世界
        wait_for_other = StateOperationNode('等待大世界', self._wait_in_world)
        edges.append(StateOperationEdge(use, wait_for_other))

        super().__init__(ctx,
                         op_name=gt('快速恢复', 'ui'),
                         edges=edges
                         )

        self.max_consumable_cnt: int = max_consumable_cnt  # 最多使用的消耗品个数
        self.quirky_snacks: bool = quirky_snacks  # 只使用奇巧零食

    def handle_init(self) -> Optional[OperationOneRoundResult]:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        可以返回初始化后判断的结果
        - 成功时跳过本指令
        - 失败时立刻返回失败
        - 不返回时正常运行本指令
        """
        self.op_result: UseTechniqueResult = UseTechniqueResult()

        return None

    def _use(self) -> OperationOneRoundResult:
        screen = self.screenshot()
        return FastRecover.handle_consumable_dialog(self, self.ctx, screen, self.op_result,
                                                    max_consumable_cnt=self.max_consumable_cnt,
                                                    quirky_snacks=self.quirky_snacks)

    def _wait_in_world(self):
        """
        使用后判断是否在大世界
        这里需要足够快的判断 方便后续的指令进行 因此尽量等待少的时间
        :return:
        """
        # 没有出现过对话框 那么直接返回即可
        if not self.op_result.with_dialog:
            return self.round_success(data=self.op_result)

        screen = self.screenshot()
        if screen_state.is_normal_in_world(screen, self.ctx.im):
            return self.round_success(data=self.op_result)
        else:
            return self.round_retry(status='未在大世界画面', wait=0.1)

    @staticmethod
    def handle_consumable_dialog(
            op: Operation,
            ctx: Context,
            screen: MatLike,
            op_result: UseTechniqueResult,
            max_consumable_cnt,
            quirky_snacks: bool,
    ) -> OperationOneRoundResult:
        if max_consumable_cnt == 0:  # 不可以使用消耗品 点击退出
            area = ScreenDialog.FAST_RECOVER_CANCEL.value
            click = op.find_and_click_area(area, screen)
            if click == Operation.OCR_CLICK_SUCCESS:
                # 没有使用消耗品的情况 退出对话框后 要尽快识别到在大世界了 方便后续指令 因此不等待
                return op.round_success(FastRecover.STATUS_NO_USE_CONSUMABLE, data=op_result)
            else:
                return op.round_retry('点击%s失败' % area.status, wait=1)
        elif op.find_area(ScreenDialog.FAST_RECOVER_NO_CONSUMABLE.value, screen):  # 没有消耗品可以使用
            area = ScreenDialog.FAST_RECOVER_CANCEL.value
            click = op.find_and_click_area(area, screen)
            if click == Operation.OCR_CLICK_SUCCESS:
                if op_result.use_consumable_times > 0:
                    # 使用了消耗品的情况 退出对话框后 需要尽快识别到在大世界了 方便再使用秘技 因此不等待
                    return op.round_success(FastRecover.STATUS_USE_CONSUMABLE, data=op_result)
                else:
                    # 没有使用消耗品的情况 退出对话框后 要尽快识别到在大世界了 方便后续指令 因此不等待
                    ctx.no_technique_recover_consumables = True  # 设置没有药可以用了
                    return op.round_success(FastRecover.STATUS_NO_USE_CONSUMABLE, data=op_result)
            else:
                return op.round_retry('点击%s失败' % area.status, wait=1)
        elif max_consumable_cnt > 0 and op_result.use_consumable_times >= max_consumable_cnt:  # 已经用了足够的消耗品了
            area = ScreenDialog.FAST_RECOVER_CANCEL.value
            click = op.find_and_click_area(area, screen)
            if click == Operation.OCR_CLICK_SUCCESS:
                # 使用了消耗品的情况 退出对话框后 需要尽快识别到在大世界了 方便再使用秘技 因此不等待
                return op.round_success(FastRecover.STATUS_USE_CONSUMABLE, data=op_result)
            else:
                return op.round_retry('点击%s失败' % area.status, wait=1)
        else:  # 还需要使用消耗品
            if quirky_snacks and not op_result.consumable_chosen:  # 理论上只有第1次需要选择 即还没有使用任何消耗品
                choose = FastRecover.choose_consumable(op, screen)
                if not choose:
                    ctx.no_technique_recover_consumables = True
                    area = ScreenDialog.FAST_RECOVER_CANCEL.value
                    click = op.find_and_click_area(area, screen)
                    if click == Operation.OCR_CLICK_SUCCESS:
                        # 没有选择到目标消耗品 因此是没有使用消耗品的情况 退出对话框后 需要尽快识别到在大世界了 方便后续指令 因此不等待
                        return op.round_success(FastRecover.STATUS_NO_USE_CONSUMABLE, data=op_result)
                    else:
                        return op.round_retry('点击%s失败' % area.status, wait=1)
                else:
                    op_result.consumable_chosen = True

            area = ScreenDialog.FAST_RECOVER_CONFIRM.value
            click = op.find_and_click_area(area, screen)
            if click == Operation.OCR_CLICK_SUCCESS:
                op_result.use_consumable_times += 1
                return op.round_wait(FastRecover.STATUS_USE_CONSUMABLE, wait=0.5, data=op_result)
            elif click == Operation.OCR_CLICK_NOT_FOUND:  # 使用满了
                area = ScreenDialog.FAST_RECOVER_CANCEL.value
                click = op.find_and_click_area(area, screen)
                if click == Operation.OCR_CLICK_SUCCESS:
                    if op_result.use_consumable_times > 0:
                        # 使用了消耗品的情况 退出对话框后 需要尽快识别到在大世界了 方便再使用秘技 因此不等待
                        return op.round_success(FastRecover.STATUS_USE_CONSUMABLE, data=op_result)
                    else:
                        # 没有使用消耗品的情况 退出对话框后 要尽快识别到在大世界了 方便后续指令 因此不等待
                        return op.round_success(FastRecover.STATUS_NO_USE_CONSUMABLE, data=op_result)
                else:
                    return op.round_retry('点击%s失败' % area.status, wait=1)
            else:
                return op.round_retry('点击%s失败' % area.status, wait=1)

    @staticmethod
    def choose_consumable(op: Operation, screen: MatLike) -> bool:
        """
        选择特定的消耗品 目前固定使用
        :param op: 当前运行的指令
        :param screen:
        :return: 是否找到目标消耗品
        """
        click = op.find_and_click_area(ScreenDialog.QUIRKY_SNACKS.value, screen)
        return True if click else False

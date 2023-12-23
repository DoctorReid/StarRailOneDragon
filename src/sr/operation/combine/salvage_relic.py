import time
from typing import List, ClassVar, Union, Optional

from cv2.typing import MatLike

from basic import Rect, Point, str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.const import phone_menu_const
from sr.const.traing_mission_const import MISSION_SALVAGE_RELIC
from sr.context import Context
from sr.operation import Operation, OperationOneRoundResult
from sr.operation.combine import StatusCombineOperation, StatusCombineOperationEdge
from sr.operation.unit.choose_inventory_category import ChooseInventoryCategory, INVENTORY_CATEGORY_RELICS
from sr.operation.unit.menu.click_phone_menu_item import ClickPhoneMenuItem
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu
from sr.operation.unit.ocr_click_one_line import OcrClickOneLine


class DoSalvageRelic(Operation):

    FILTER_POS: ClassVar[Point] = Point(547, 988)  # 左下角筛选的按钮
    FILTER_RULE_RECT: ClassVar[Rect] = Rect(1406, 99, 1540, 138)  # 右侧 筛选规则 为时
    RARITY_RECT: ClassVar[Rect] = Rect(1406, 321, 1821, 435)  # 右侧 稀有度筛选框
    ALL_RECT: ClassVar[Rect] = Rect(984, 967, 1048, 999)
    SALVAGE_RECT: ClassVar[Rect] = Rect(1589, 970, 1740, 1003)
    CONFIRM_RECT: ClassVar[Rect] = Rect(1095, 801, 1250, 836)
    CONTINUE_RECT: ClassVar[Rect] = Rect(688, 918, 1236, 977)

    def __init__(self, ctx: Context):
        """
        需要在【遗器分解】页面使用 执行分解部分
        分解成功后逗留在【遗器分解】页面
        """
        super().__init__(ctx, try_times=5, op_name='%s %s' % (gt('遗器分解', 'ui'), gt('执行', 'ui')))
        self.phase: int = 0

    def _init_before_execute(self):
        super()._init_before_execute()
        self.phase = 0

    def _execute_one_round(self) -> OperationOneRoundResult:
        if self.phase == 0:  # 点击过滤
            self.ctx.controller.click(DoSalvageRelic.FILTER_POS)
            time.sleep(2)
            if self._filter_shown():
                self.phase += 1
                return Operation.round_wait(wait=1)
            else:
                return Operation.round_retry('点击筛选失败', wait=1)
        elif self.phase == 1:  # 选择3、4星
            if self._choose_filter():
                self.phase += 1
                return Operation.round_wait()
            else:
                return Operation.round_retry('点击筛选条件失败', wait=1)
        elif self.phase == 2:  # 点击空白 回到分解主页
            self.ctx.controller.click(DoSalvageRelic.ALL_RECT.center)
            if self._filter_shown():
                return Operation.round_retry('未能退出筛选', wait=1)
            else:
                self.phase += 1
                return Operation.round_wait(wait=1)
        elif self.phase == 3:  # 全选并分解
            if not self._click_salvage():
                return Operation.round_retry('点击分解失败', wait=1)
            else:
                if self._tip_shown():  # TODO 需要确定3星遗器会不会出现提示
                    self.phase += 1
                    return Operation.round_wait(wait=1)
                else:
                    return Operation.round_retry('未出现提示', wait=1)
        elif self.phase == 4:  # 点击确认
            screen = self.screenshot()
            if not self._tip_shown(screen):
                return Operation.round_retry('未出现提示', wait=1)
            else:
                click = self.ocr_and_click_one_line('确认', DoSalvageRelic.CONFIRM_RECT, screen)
                if click == Operation.OCR_CLICK_SUCCESS:
                    self.phase += 1
                    return Operation.round_wait(wait=1)
                else:
                    return Operation.round_retry('点击确认失败')
        elif self.phase == 5:  # 点击空白继续
            screen = self.screenshot()
            click = self.ocr_and_click_one_line('点击空白处关闭', DoSalvageRelic.CONTINUE_RECT, screen)
            if click == Operation.OCR_CLICK_SUCCESS:
                return Operation.round_success()
            else:
                return Operation.round_retry('点击空白继续失败', wait=1)

    def _filter_shown(self, screen: Optional[MatLike] = None):
        """
        过滤器是否显示出来
        :param screen: 屏幕截图
        :return:
        """
        if screen is None:
            screen = self.screenshot()

        part, _ = cv2_utils.crop_image(screen, DoSalvageRelic.FILTER_RULE_RECT)
        ocr_str = self.ctx.ocr.ocr_for_single_line(part)

        return str_utils.find_by_lcs(gt('筛选规则', 'ocr'), ocr_str, percent=0.1)

    def _choose_filter(self, screen: Optional[MatLike] = None, click: bool = True) -> bool:
        """
        按过滤规则选择
        目前固定选择3、4星
        :param screen: 屏幕截图
        :param click: 是否需要点击
        :return: 是否有找到目标并点击
        """
        if screen is None:
            screen = self.screenshot()

        part, _ = cv2_utils.crop_image(screen, DoSalvageRelic.RARITY_RECT)

        ocr_result_map = self.ctx.ocr.match_words(part, words=['3', '4'])

        if len(ocr_result_map) == 0:
            return False

        find = False
        for mrl in ocr_result_map.values():
            if mrl.max is not None:
                find = True
                if click:
                    self.ctx.controller.click(DoSalvageRelic.RARITY_RECT.left_top + mrl.max.center)
                    time.sleep(0.5)

        return find

    def _click_salvage(self, screen: Optional[MatLike] = None) -> bool:
        """
        点击【全选】-【分解】
        :param screen: 屏幕截图
        :return: 是否点击成功
        """
        if screen is None:
            screen = self.screenshot()

        click_all = self.ocr_and_click_one_line('全选', DoSalvageRelic.ALL_RECT, screen)
        if click_all != Operation.OCR_CLICK_SUCCESS:
            return False

        time.sleep(1.5)
        click_salvage = self.ocr_and_click_one_line('分解', DoSalvageRelic.SALVAGE_RECT, screen)
        if click_salvage != Operation.OCR_CLICK_SUCCESS:
            return False

        time.sleep(1.5)
        return True

    def _tip_shown(self, screen: Optional[MatLike] = None) -> bool:
        """
        是否显示出【提示】框
        :param screen:
        :return: 是否显示
        """
        if screen is None:
            screen = self.screenshot()

        part, _ = cv2_utils.crop_image(screen, DoSalvageRelic.CONFIRM_RECT)
        ocr_str = self.ctx.ocr.ocr_for_single_line(part)

        return str_utils.find_by_lcs(gt('确认', 'ocr'), ocr_str, percent=0.1)


class SalvageRelic(StatusCombineOperation):

    SALVAGE_BTN_RECT: ClassVar[Rect] = Rect(1210, 975, 1320, 1010)

    def __init__(self, ctx: Context):
        """
        分解遗器 只会挑选3、4星遗器
        :param ctx: 上下文
        """
        ops: List[Operation] = []
        edges: List[StatusCombineOperationEdge] = []

        open_menu = OpenPhoneMenu(ctx)  # 打开菜单
        ops.append(open_menu)

        inventory = ClickPhoneMenuItem(ctx, phone_menu_const.INVENTORY)  # 打开背包
        ops.append(inventory)
        edges.append(StatusCombineOperationEdge(open_menu, inventory))

        choose_relics_tab = ChooseInventoryCategory(ctx, INVENTORY_CATEGORY_RELICS)  # 遗器
        ops.append(choose_relics_tab)
        edges.append(StatusCombineOperationEdge(inventory, choose_relics_tab))

        click_salvage = OcrClickOneLine(ctx, rect=SalvageRelic.SALVAGE_BTN_RECT, target_cn='分解')  # 点击分解
        ops.append(click_salvage)
        edges.append(StatusCombineOperationEdge(choose_relics_tab, click_salvage))

        do_salvage = DoSalvageRelic(ctx)  # 执行分解
        ops.append(do_salvage)
        edges.append(StatusCombineOperationEdge(click_salvage, do_salvage))

        back_to_menu = OpenPhoneMenu(ctx)  # 返回菜单
        ops.append(back_to_menu)
        edges.append(StatusCombineOperationEdge(do_salvage, back_to_menu))

        StatusCombineOperation.__init__(self, ctx, ops, edges,
                                        op_name='%s %s' % (gt('实训任务', 'ui'), gt(MISSION_SALVAGE_RELIC.id_cn, 'ui'))
                                        )

from typing import Optional

from basic import str_utils, Point
from basic.i18_utils import gt
from basic.img import cv2_utils, MatchResult
from sr.const import phone_menu_const
from sr.context.context import Context
from sr.operation import StateOperation, OperationOneRoundResult, StateOperationNode
from sr.operation.common.back_to_normal_world_plus import BackToNormalWorldPlus
from sr.operation.unit.menu.click_phone_menu_item import ClickPhoneMenuItem
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu
from sr.synthesize.synthesize_const import ScreenSynthesize, SynthesizeItem


class Synthesize(StateOperation):

    def __init__(self, ctx: Context, item: SynthesizeItem, num: int):
        """
        如果不在合成页面 则进入合成页面
        合成指定物品后 停留在指定页面
        :param ctx: 上下文
        :param item: 要合成的物品
        :param num: 要合成的数量 0为最大值。当前只支持最大值
        """
        super().__init__(ctx, try_times=5,
                         op_name='%s %s' % (gt('合成', 'ui'), ''))

        self.item: SynthesizeItem = item  # 要合成的物品
        self.num: int = num  # 要合成的数量 0为最大值

    def add_edges_and_nodes(self) -> None:
        """
        初始化前 添加边和节点 由子类实行
        :return:
        """
        check_screen = StateOperationNode('识别画面', self.check_screen)

        first_to_world = StateOperationNode('返回大世界', op=BackToNormalWorldPlus(self.ctx))
        self.add_edge(check_screen, first_to_world)

        open_menu = StateOperationNode('打开菜单', op=OpenPhoneMenu(self.ctx))
        self.add_edge(first_to_world, open_menu)

        choose_synthesize = StateOperationNode('选择合成', op=ClickPhoneMenuItem(self.ctx, phone_menu_const.SYNTHESIZE))
        self.add_edge(open_menu, choose_synthesize)

        choose_category = StateOperationNode('选择合成类别', self.choose_category)
        self.add_edge(choose_synthesize, choose_category)
        self.add_edge(check_screen, choose_category, status=ScreenSynthesize.TITLE.value.status)

        choose_item = StateOperationNode('选择合成物品', self.choose_item)
        self.add_edge(choose_category, choose_item)

        choose_num = StateOperationNode('选择数量', self.choose_num)
        self.add_edge(choose_item, choose_num)

        click_synthesize = StateOperationNode('点击合成', self.click_synthesize)
        self.add_edge(choose_num, click_synthesize)

        click_confirm = StateOperationNode('点击确认', self.click_confirm)
        self.add_edge(click_synthesize, click_confirm)

        click_empty = StateOperationNode('点击空白处关闭', self.click_empty)
        self.add_edge(click_confirm, click_empty)

    def check_screen(self) -> OperationOneRoundResult:
        """
        识别画面
        :return:
        """
        screen = self.screenshot()
        title = ScreenSynthesize.TITLE.value

        if self.find_area(screen=screen, area=title):
            return self.round_success(status=title.status)
        else:
            return self.round_success()

    def choose_category(self) -> OperationOneRoundResult:
        """
        选择合成类别
        :return:
        """
        category = self.item.category

        screen = self.screenshot()
        area = ScreenSynthesize.CATEGORY_TITLE.value
        part = cv2_utils.crop_image_only(screen, area)

        ocr_result = self.ctx.ocr.ocr_for_single_line(part)
        if str_utils.find_by_lcs(ocr_result, gt(category.name, 'ocr'), percent=0.5):
            return self.round_success()
        else:
            self.ctx.controller.click(category.area.center)
            return self.round_retry(wait=0.5)

    def choose_item(self) -> OperationOneRoundResult:
        """
        选择合成物品
        :return:
        """
        screen = self.screenshot()
        area = ScreenSynthesize.ITEM_LIST.value
        result = self.get_item_pos(screen)

        if result is None:
            drag_from = area.center
            drag_to = drag_from + Point(0, -100)
            self.ctx.controller.drag_to(start=drag_from, end=drag_to)
            return self.round_retry(f'未找到{self.item.name}', wait=0.5)
        else:
            self.ctx.controller.click(result.center)
            return self.round_success(wait=0.5)

    def get_item_pos(self, screen) -> Optional[MatchResult]:
        """
        获取合成物品的位置
        :param screen:
        :return:
        """
        area = ScreenSynthesize.ITEM_LIST.value
        part = cv2_utils.crop_image_only(screen, area)

        mrl = self.ctx.im.match_template(part, self.item.template_id, template_sub_dir='consumable')

        if mrl.max is None:
            return None

        result = mrl.max
        result.x += area.rect.left_top.x
        result.y += area.rect.left_top.y

        return result

    def choose_num(self) -> OperationOneRoundResult:
        """
        选择合成数量 当前只支持最大值
        :return:
        """
        screen = self.screenshot()
        area = ScreenSynthesize.NOT_ENOUGH_MATERIAL.value
        if self.find_area(screen=screen, area=area):
            return self.round_fail(area.status)

        area = ScreenSynthesize.NUM_MAX.value
        self.ctx.controller.click(area.center)
        return self.round_success(wait=0.5)

    def click_synthesize(self) -> OperationOneRoundResult:
        """
        进行合成
        :return:
        """
        screen = self.screenshot()
        area = ScreenSynthesize.SYNTHESIZE_BTN.value
        return self.round_by_find_and_click_area(screen, area, success_wait=1, retry_wait_round=0.5)

    def click_confirm(self) -> OperationOneRoundResult:
        """
        合成出现的对话框 点击确认
        :return:
        """
        screen = self.screenshot()
        area = ScreenSynthesize.SYNTHESIZE_DIALOG_CONFIRM.value
        return self.round_by_find_and_click_area(screen, area, success_wait=5, retry_wait_round=0.5)

    def click_empty(self) -> OperationOneRoundResult:
        """
        确认后 点击空白关闭
        :return:
        """
        screen = self.screenshot()
        area = ScreenSynthesize.SYNTHESIZE_EMPTY_TO_CLOSE.value
        return self.round_by_find_and_click_area(screen, area, success_wait=1, retry_wait_round=0.5)

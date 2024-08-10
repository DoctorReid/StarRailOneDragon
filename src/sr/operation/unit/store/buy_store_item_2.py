from typing import Optional

from cv2.typing import MatLike

from basic import Point, str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.context.context import Context, get_context
from sr.operation import StateOperation, OperationOneRoundResult, StateOperationNode
from sr.operation.unit.store.store_const import StoreItem, ScreenStore, StoreItemEnum
from sr.screen_area.screen_normal_world import ScreenNormalWorld


class BuyStoreItem2(StateOperation):

    def __init__(self, ctx: Context, item: StoreItem, buy_num: int):
        """
        在一个商店页面使用
        购买商品后 最后停留在商店页面
        :param ctx: 上下文
        :param item: 要购买的商品
        :param buy_num: 要购买的数量 0的话代表最大值
        """
        super().__init__(ctx, try_times=5,
                         op_name='%s %s' % (gt('购买商品', 'ui'), gt(item.cn, 'ui'))
                         )

        self.item: StoreItem = item  # 要购买的商品
        self.buy_num: int = buy_num  # 要购买的数量

    def add_edges_and_nodes(self) -> None:
        """
        初始化前 添加边和节点 由子类实行
        :return:
        """
        choose_item = StateOperationNode('选择商品', self.choose_item)

        choose_buy_num = StateOperationNode('选择数量', self.choose_buy_num)
        self.add_edge(choose_item, choose_buy_num)

        buy_confirm = StateOperationNode('确认购买', self.buy_confirm)
        self.add_edge(choose_buy_num, buy_confirm)

        click_empty = StateOperationNode('点击空白处关闭', self.click_empty)
        self.add_edge(buy_confirm, click_empty)

    def choose_item(self) -> OperationOneRoundResult:
        """
        选择商品
        :return:
        """
        screen = self.screenshot()
        pos = self.get_item_pos(screen)
        if pos is None:  # 找不到的时候 向下滑动
            start_point = ScreenStore.STORE_ITEM_LIST.value.center
            end_point = start_point + Point(0, - 100)
            self.ctx.controller.drag_to(end_point, start_point)
            return self.round_retry(status=f'未找到商品{self.item.cn}', wait=0.5)
        else:
            self.ctx.controller.click(pos)
            return self.round_success(wait=0.5)

    def get_item_pos(self, screen: MatLike) -> Optional[Point]:
        """
        获取商品的位置
        :param screen: 游戏画面
        :return:
        """
        area = ScreenStore.STORE_ITEM_LIST.value
        part = cv2_utils.crop_image_only(screen, area.rect)

        mrl = self.ctx.im.match_template(part, template_id=self.item.template_id, template_sub_dir='store',
                                         ignore_template_mask=True)
        if mrl.max is None:
            return None
        else:
            return mrl.max.center + area.rect.left_top

    def choose_buy_num(self) -> OperationOneRoundResult:
        """
        选择购买数量 暂时只支持全量
        :return:
        """
        screen = self.screenshot()
        area = ScreenStore.BUY_DIALOG_MAX_BTN.value
        return self.round_by_find_and_click_area(screen, area, success_wait=0.25)

    def buy_confirm(self) -> OperationOneRoundResult:
        """
        点击确认 不能购买时点击取消
        :return:
        """
        screen = self.screenshot()
        sold_out = ScreenStore.BUY_DIALOG_SOLD_OUT.value
        no_money = ScreenStore.BUY_DIALOG_NO_MONEY.value

        part = cv2_utils.crop_image_only(screen, sold_out.rect)
        ocr_result = self.ctx.ocr.run_ocr_single_line(part)

        if (str_utils.find_by_lcs(ocr_result, gt(sold_out.text, 'ocr'), percent=sold_out.lcs_percent)
            or str_utils.find_by_lcs(ocr_result, gt(no_money.text, 'ocr'), percent=no_money.lcs_percent)):
            click_area = ScreenStore.BUY_DIALOG_CANCEL_BTN.value
        else:
            click_area = ScreenStore.BUY_DIALOG_CONFIRM_BTN.value

        round_result = self.round_by_find_and_click_area(screen, click_area, success_wait=0.5, retry_wait_round=1)
        if round_result.is_success:
            if click_area == ScreenStore.BUY_DIALOG_CONFIRM_BTN.value:
                return self.round_success(wait=1)
            else:
                return self.round_fail('购买失败')
        else:
            return round_result

    def click_empty(self) -> OperationOneRoundResult:
        """
        够买后 点击空白处关闭
        :return:
        """
        screen = self.screenshot()
        area = ScreenNormalWorld.EMPTY_TO_CLOSE.value
        return self.round_by_find_and_click_area(screen, area, success_wait=1, retry_wait_round=0.5)


def __debug_op():
    ctx = get_context()
    ctx.start_running()

    op = BuyStoreItem2(ctx, StoreItemEnum.SEED.value, buy_num=0)
    op.execute()


if __name__ == '__main__':
    __debug_op()

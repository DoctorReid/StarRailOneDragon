import time

from cv2.typing import MatLike

from basic import Rect, Point, str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils, MatchResultList, MatchResult
from sr.context import Context
from sr.operation import Operation


class BuyStoreItem(Operation):

    BUY_NUM_CTRL_RECT = Rect(1330, 600, 1500, 660)
    CONFIRM_BTN_RECT = Rect(1000, 710, 1350, 770)

    def __init__(self, ctx: Context, buy_num: int = 0, buy_max: bool = True):
        """
        :param ctx:
        :param buy_num: 购买数量 优先看 buy_max
        :param buy_max: 购买最多
        """
        super().__init__(ctx, try_times=3, op_name=gt('购买商品', 'ui'))
        self.buy_num: int = buy_num
        self.buy_max: bool = buy_max

    def _execute_one_round(self) -> int:
        screen: MatLike = self.screenshot()

        if not self._click_buy_num(screen):
            time.sleep(1)
            return Operation.RETRY

        if not self._click_buy_confirm(screen):
            time.sleep(1)
            return Operation.RETRY

        return Operation.SUCCESS

    def _click_buy_num(self, screen: MatLike) -> bool:
        """
        点击到具体的购买数量
        :param screen:
        :return: 是否点击成功
        """
        part, _ = cv2_utils.crop_image(screen, BuyStoreItem.BUY_NUM_CTRL_RECT)

        template_id: str = 'store_buy_max' if self.buy_max else 'store_buy_max'

        result_list: MatchResultList = self.ctx.im.match_template(part, template_id,
                                                                  ignore_template_mask=True, only_best=True)
        result: MatchResult = result_list.max

        if result is None:
            time.sleep(1)
            return False
        # cv2_utils.show_image(part, result_list, win_name='BuyStoreItem')

        to_click: Point = result.center + BuyStoreItem.BUY_NUM_CTRL_RECT.left_top
        click_times = 1 if self.buy_max else self.buy_num - 1
        if click_times > 0:
            for _ in range(click_times):
                click_result: bool = self.ctx.controller.click(to_click)
                if not click_result:
                    return False

        return True


    def _click_buy_confirm(self, screen: MatLike) -> bool:
        """
        点击 确认 购买
        :param screen:
        :return: 是否点击成功
        """
        part, _ = cv2_utils.crop_image(screen, BuyStoreItem.CONFIRM_BTN_RECT)

        template_id: str = 'store_buy_max' if self.buy_max else 'store_buy_max'

        ocr_result: str = self.ctx.ocr.ocr_for_single_line(part, strict_one_line=True)

        if str_utils.find_by_lcs(gt('确认', 'ocr'), ocr_result, 0.3):
            return self.ctx.controller.click(BuyStoreItem.CONFIRM_BTN_RECT.center)
        else:
            return False

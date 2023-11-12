import time

import cv2
import numpy as np
from cv2.typing import MatLike

from basic import Rect, Point
from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.context import Context
from sr.operation import Operation


class ClickStoreItem(Operation):

    """
    商店购买页面 点击特定的商品
    """

    STORE_ITEM_LIST = Rect(290, 110, 1280, 430)

    def __init__(self, ctx: Context, item_name: str, lcs_percent: float):
        super().__init__(ctx, try_times=5,
                         op_name=gt('点击商品','ui') + gt(item_name, 'ui'))
        self.item_name: str = item_name
        self.lcs_percent: float = lcs_percent

    def _init_before_execute(self):
        pass

    def _execute_one_round(self) -> int:
        screen: MatLike = self.screenshot()

        part, _ = cv2_utils.crop_image(screen, ClickStoreItem.STORE_ITEM_LIST)
        lower_color = np.array([200, 200, 200], dtype=np.uint8)
        upper_color = np.array([255, 255, 255], dtype=np.uint8)
        white_part = cv2.inRange(part, lower_color, upper_color)

        # cv2_utils.show_image(white_part, 'ClickStoreItem')

        ocr_result = self.ctx.ocr.match_words(white_part, words=[self.item_name],
                                              lcs_percent=self.lcs_percent)

        if len(ocr_result) == 0:
            start_point: Point = ClickStoreItem.STORE_ITEM_LIST.center
            end_point: Point = Point(start_point.x, start_point.y - 100)
            self.ctx.controller.drag_to(end_point, start_point)
            time.sleep(0.5)
            return Operation.RETRY

        # TODO 选一个匹配程度最高的结果

        to_click: Point = ocr_result.popitem()[1].max.center + ClickStoreItem.STORE_ITEM_LIST.left_top
        click = self.ctx.controller.click(to_click)
        if click:
            return Operation.SUCCESS
        else:
            return Operation.RETRY

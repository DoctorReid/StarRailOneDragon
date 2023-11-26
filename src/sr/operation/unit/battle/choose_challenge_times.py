import time
from typing import ClassVar

from cv2.typing import MatLike

from basic import Rect, str_utils, Point
from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.context import Context
from sr.operation import Operation


class ChooseChallengeTimes(Operation):

    """
    在挑战副本的选择难度页面
    选择挑战次数
    """

    CURRENT_TIMES_RECT: ClassVar[Rect] = Rect(1470, 850, 1620, 890)
    MINUS_BTN_RECT: ClassVar[Rect] = Rect(1190, 870, 1300, 930)
    PLUS_BTN_RECT: ClassVar[Rect] = Rect(1800, 870, 1900, 930)

    def __init__(self, ctx: Context, total_times: int):
        """
        :param ctx:
        :param total_times: 总共挑战次数 <=6
        """
        super().__init__(ctx, try_times=5, op_name=gt('选择挑战次数', 'ui'))
        self.total_times: int = total_times

    def _execute_one_round(self) -> int:
        screen: MatLike = self.screenshot()

        current = self._get_current_times(screen)
        if current == 0:  # 可能界面还没有加载出来 等等
            time.sleep(0.5)
            return Operation.RETRY

        if current == self.total_times:
            return Operation.SUCCESS
        elif current < self.total_times:
            if self._click_plus(screen, self.total_times - current):
                return Operation.WAIT
        else:
            if self._click_minus(screen, self.total_times - current):
                return Operation.WAIT

    def _get_current_times(self, screen: MatLike) -> int:
        """
        判断当前选择的次数
        :param screen: 屏幕截图
        :return: 当前选择次数
        """
        part, _ = cv2_utils.crop_image(screen, ChooseChallengeTimes.CURRENT_TIMES_RECT)
        # cv2_utils.show_image(part, win_name='_get_current_times')
        ocr_result = self.ctx.ocr.ocr_for_single_line(part, strict_one_line=True)
        return str_utils.get_positive_digits(ocr_result)

    def _click_plus(self, screen: MatLike, click_times: int) -> bool:
        """
        找到加号并点击
        :param screen: 屏幕截图
        :param click_times: 需要点击的次数
        :return: 是否点击成功
        """
        part, _ = cv2_utils.crop_image(screen, ChooseChallengeTimes.PLUS_BTN_RECT)
        result_list = self.ctx.im.match_template(part, 'battle_times_plus', ignore_template_mask=True, only_best=True)
        result = result_list.max

        if result is None:
            return False

        to_click: Point = result.center + ChooseChallengeTimes.PLUS_BTN_RECT.left_top
        for _ in range(click_times):
            if not self.ctx.controller.click(to_click):
                return False
            time.sleep(0.2)

        return True

    def _click_minus(self, screen: MatLike, click_times: int) -> bool:
        """
        找到减号并点击
        :param screen: 屏幕截图
        :param click_times: 需要点击的次数
        :return: 是否点击成功
        """
        part, _ = cv2_utils.crop_image(screen, ChooseChallengeTimes.MINUS_BTN_RECT)
        result_list = self.ctx.im.match_template(part, 'battle_times_minus', ignore_template_mask=True, only_best=True)
        result = result_list.max

        if result is None:
            return False

        to_click: Point = result.center + ChooseChallengeTimes.MINUS_BTN_RECT.left_top
        for _ in range(click_times):
            if not self.ctx.controller.click(to_click):
                return False
            time.sleep(0.2)

        return True

import time
from typing import ClassVar

from cv2.typing import MatLike

from basic import str_utils, Rect
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr.context import Context
from sr.image.sceenshot import secondary_ui
from sr.operation import Operation, OperationOneRoundResult


class CheckForgottenHallStar(Operation):
    """
    需要先在忘却之庭选择关卡的页面
    检测右下角数字判断当前星数
    返回附加状态 = 成功时是当前星数，失败时是原因
    """

    _STAR_RECT: ClassVar[Rect] = Rect(1665, 950, 1725, 995)

    def __init__(self, ctx: Context, star_callback=None):
        super().__init__(ctx, try_times=5,
                         op_name='%s %s' % (gt('忘却之庭', 'ui'), gt('星数', 'ui'))
                         )
        self.star_callback = star_callback  # 获取星数的回调

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen: MatLike = self.screenshot()

        if not secondary_ui.in_secondary_ui(screen, self.ctx.ocr, secondary_ui.TITLE_FORGOTTEN_HALL.cn):
            log.info('等待忘却之庭加载')
            time.sleep(1)
            return Operation.round_retry('未进入 ' + secondary_ui.TITLE_FORGOTTEN_HALL.cn)

        star = self._get_star_cnt(screen)

        if star == -1:
            time.sleep(1)
            return Operation.round_retry('获取不到星数')
        elif star > 30:
            time.sleep(1)
            return Operation.round_retry('星数值异常 %d' % star)
        else:
            if self.star_callback is not None:
                self.star_callback(star)
            return Operation.round_success(str(star))

    def _get_star_cnt(self, screen: MatLike) -> int:
        """
        获取星数
        :param screen: 屏幕截图
        :return: 星数。如果没有获取到就返回-1
        """
        part, _ = cv2_utils.crop_image(screen, CheckForgottenHallStar._STAR_RECT)
        # cv2_utils.show_image(part, win_name='_get_star_cnt')
        ocr_str = self.ctx.ocr.ocr_for_single_line(part, strict_one_line=True)
        return str_utils.get_positive_digits(ocr_str, -1)

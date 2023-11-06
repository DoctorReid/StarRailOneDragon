import time

from cv2.typing import MatLike

from basic import Point
from basic.i18_utils import gt
from basic.img import MatchResult
from sr.const.phone_menu_const import PhoneMenuItem
from sr.context import Context
from sr.image.sceenshot import phone_menu
from sr.operation import Operation


class ClickPhoneMenuItem(Operation):

    """
    点击菜单中的某个特定的项
    需要先保证在菜单页面上
    """

    def __init__(self, ctx: Context, item: PhoneMenuItem):
        super().__init__(ctx, try_times=10, op_name=gt('点击菜单 %s', 'ui') % gt(item.cn, 'ui'))
        self.item: PhoneMenuItem = item

    def run(self) -> int:
        screen: MatLike = self.screenshot()

        result: MatchResult = phone_menu.get_phone_menu_item_pos(screen, self.ctx.im, self.item)

        if result is None:  # 没找到的情况 上下随机滑动
            self.scroll_menu_area(1 if self.op_round % 2 == 1 else -1)
            time.sleep(0.5)
            return Operation.RETRY
        else:
            r = self.ctx.controller.click(result.center())
            time.sleep(0.5)
            return Operation.SUCCESS if r else Operation.RETRY

    def scroll_menu_area(self, d: int = 1):
        """
        在菜单区域的地方滚动鼠标
        :param d: 滚动距离 正向下 负向上
        :return:
        """
        x1, y1 = phone_menu.MENU_ITEMS_PART.center.tuple()
        x2, y2 = x1, y1 + d * -200
        self.ctx.controller.drag_to(start=Point(x1, y1), end=Point(x2, y2), duration=0.5)
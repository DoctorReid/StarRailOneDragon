import time

from cv2.typing import MatLike

from basic.i18_utils import gt
from basic.img import MatchResult
from sr.const.phone_menu_const import PhoneMenuItem
from sr.context.context import Context
from sr.image.sceenshot import phone_menu
from sr.operation import Operation


class ClickPhoneMenuItemAtRight(Operation):

    """
    点击菜单侧栏中的某个特定的项（右边的小图标）
    需要先保证在菜单页面上
    """

    def __init__(self, ctx: Context, item: PhoneMenuItem):
        super().__init__(ctx, try_times=5, op_name=gt('点击菜单侧栏 %s', 'ui') % gt(item.cn, 'ui'))
        self.item: PhoneMenuItem = item

    def _execute_one_round(self) -> int:
        screen: MatLike = self.screenshot()

        result: MatchResult = phone_menu.get_phone_menu_item_pos_at_right(screen, self.ctx.im, self.item)

        if result is None:  # 没找到的情况 上下随机滑动
            time.sleep(0.5)
            return Operation.RETRY
        else:
            r = self.ctx.controller.click(result.center)
            time.sleep(0.5)
            return Operation.SUCCESS if r else Operation.RETRY

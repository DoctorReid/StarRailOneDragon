from cv2.typing import MatLike
from enum import Enum

from one_dragon.base.screen import screen_utils
from one_dragon.base.screen.screen_utils import FindAreaResultEnum
from sr_od.context.sr_context import SrContext


class ScreenState(Enum):

    FAST_RECOVER = '快速恢复'


def is_fast_recover(ctx: SrContext, screen: MatLike) -> bool:
    """
    是否在快速恢复画面
    :param ctx: 上下文
    :param screen: 游戏画面
    :return:
    """
    return screen_utils.find_area(ctx, screen, '快速恢复对话框', '快速恢复标题') == FindAreaResultEnum.TRUE
from cv2.typing import MatLike
from enum import Enum

from one_dragon.base.screen import screen_utils
from one_dragon.base.screen.screen_utils import FindAreaResultEnum
from sr_od.context.sr_context import SrContext


class ScreenState(Enum):

    BATTLE: str = '战斗'
    BATTLE_FAIL: str = '战斗失败'


def is_battle_fail(ctx: SrContext, screen: MatLike) -> bool:
    """
    是否在战斗失败画面
    :param ctx: 上下文
    :param screen: 游戏画面
    :return:
    """
    return screen_utils.find_area(ctx, screen, '战斗画面', '战斗失败') == FindAreaResultEnum.TRUE
import time

from sr.context import Context
from sr.image.sceenshot import battle
from sr.operation import Operation


class WaitInWorld(Operation):

    """
    等待加载 直到进入游戏主界面 右上角有角色图标
    """

    def __init__(self, ctx: Context, wait: int = 10):
        """
        :param ctx:
        :param wait: 最多等待多少秒
        """
        super().__init__(ctx, try_times=wait)

    def run(self) -> int:
        screen = self.screenshot()
        if battle.IN_WORLD == battle.get_battle_status(screen, self.ctx.im):
            return Operation.SUCCESS

        time.sleep(1)
        return Operation.RETRY

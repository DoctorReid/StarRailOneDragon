import time

from basic.i18_utils import gt
from sr.context import Context
from sr.image.sceenshot import battle
from sr.operation import Operation


class WaitInWorld(Operation):

    """
    等待加载 直到进入游戏主界面 右上角有角色图标
    """

    def __init__(self, ctx: Context, wait: float = 20):
        """
        :param ctx:
        :param wait: 最多等待多少秒
        """
        super().__init__(ctx, op_name=gt('等待主界面'))
        self.timeout_seconds: float = float(wait)
        self.start_time = 0

    def _init_before_execute(self):
        self.start_time = time.time()

    def _execute_one_round(self) -> int:
        screen = self.screenshot()
        if battle.IN_WORLD == battle.get_battle_status(screen, self.ctx.im):
            time.sleep(1)  # 多等待一秒 动画后界面完整显示需要点时间
            return Operation.SUCCESS

        time.sleep(1)
        if time.time() - self.start_time > self.timeout_seconds:
            return Operation.FAIL
        return Operation.WAIT

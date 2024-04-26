import time
from typing import Callable, Optional

from basic.i18_utils import gt
from sr.context import Context
from sr.image.sceenshot import screen_state
from sr.operation import Operation, OperationResult, OperationOneRoundResult


class WaitInWorld(Operation):

    """
    等待加载 直到进入游戏主界面 右上角有角色图标
    """

    def __init__(self, ctx: Context, wait: float = 20,
                 wait_after_success: float = 0,
                 op_callback: Optional[Callable[[OperationResult], None]] = None):
        """
        :param ctx:
        :param wait: 最多等待多少秒
        :param op_callback: 回调
        """
        super().__init__(ctx, op_name=gt('等待主界面'), timeout_seconds=wait,
                         op_callback=op_callback)
        self.wait_after_success: float = wait_after_success

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()
        if screen_state.is_normal_in_world(screen, self.ctx.im):
            return Operation.round_success(wait=self.wait_after_success)

        return Operation.round_wait(wait=1)


class WaitInSeconds(Operation):
    """
    等待一定秒数 可以用在
    1. 疾跑后固定在原地再操作
    """

    def __init__(self, ctx: Context, seconds: float = 10):
        """
        :param ctx:
        :param seconds: 等待多少秒
        """
        super().__init__(ctx, op_name=gt('等待秒数 %.2f') % seconds)
        self.seconds: float = float(seconds)

    def _execute_one_round(self) -> int:
        time.sleep(self.seconds)
        return Operation.SUCCESS

import time

from basic.i18_utils import gt
from sr.context import Context
from sr.operation import Operation


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

    def run(self) -> int:
        time.sleep(self.seconds)
        return Operation.SUCCESS
import time

from basic.log_utils import log
from sr.context import Context


class Operation:
    """
    基础动作
    本身可暂停 但不由自身恢复
    """

    RETRY = 0  # 重试
    SUCCESS = 1  # 成功
    WAIT = 2  # 等待 本轮不计入
    FAIL = -1  # 失败

    def __init__(self, ctx: Context, try_times: int = 1):
        self.try_times: int = try_times
        self.op_round: int = 0
        self.ctx: Context = ctx
        self.round_running: bool = False
        ctx.register_pause(self, self.on_pause, self.on_resume)

    def execute(self) -> bool:
        """
        循环执系列动作直到完成为止
        """
        result: int = Operation.RETRY
        while self.op_round < self.try_times:
            if not self.ctx.running:
                time.sleep(1)
                continue
            self.round_running = True
            self.op_round += 1
            result = self.run()
            self.round_running = False
            if result == Operation.RETRY:
                continue
            elif result == Operation.SUCCESS:
                result = True
                break
            elif result == Operation.FAIL:
                result = False
                break
            elif result == Operation.WAIT:
                self.op_round -= 1
                continue
            else:
                log.error('动作执行返回结果错误 %s', result)
                result = False
                break
        self.ctx.unregister(self)
        return result

    def run(self) -> int:
        pass

    def on_pause(self):
        while self.round_running:
            time.sleep(1)

    def on_resume(self):
        pass
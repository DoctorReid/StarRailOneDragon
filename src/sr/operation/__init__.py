import time

from cv2.typing import MatLike

from basic.img.os import save_debug_image
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

    def __init__(self, ctx: Context, try_times: int = 2):
        self.try_times: int = try_times
        self.op_round: int = 0
        self.ctx: Context = ctx
        ctx.register_pause(self, self.on_pause, self.on_resume)
        self.last_screenshot: MatLike = None

    def execute(self) -> bool:
        """
        循环执系列动作直到完成为止
        """
        result: int = Operation.RETRY
        while self.op_round < self.try_times:
            if self.ctx.running == 0:
                return False
            elif self.ctx.running == 2:
                time.sleep(1)
                continue

            self.op_round += 1
            try:
                self.last_screenshot = None
                result = self.run()
            except Exception as e:
                if self.last_screenshot is not None:
                    file_name = save_debug_image(self.last_screenshot, prefix=self.__class__.__name__)
                    log.error('指令执行出错 相关截图保存至 %s', file_name, exc_info=True)
                else:
                    log.error('指令执行出错', exc_info=True)
                result = Operation.RETRY

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
        pass

    def on_resume(self):
        pass

    def screenshot(self):
        """
        包装一层截图 会在内存中保存上一张截图 方便出错时候保存
        :return:
        """
        self.last_screenshot = self.ctx.controller.screenshot()
        return self.last_screenshot

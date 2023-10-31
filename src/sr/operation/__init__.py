import time

from cv2.typing import MatLike

from basic.img.os import save_debug_image
from basic.log_utils import log
from sr.config import game_config
from sr.config.game_config import GameConfig
from sr.context import Context
from sr.image.sceenshot import fill_uid_black


class Operation:
    """
    基础动作
    本身可暂停 但不由自身恢复
    """

    RETRY = 0  # 重试
    SUCCESS = 1  # 成功
    WAIT = 2  # 等待 本轮不计入
    FAIL = -1  # 失败

    def __init__(self, ctx: Context, try_times: int = 2, op_name: str = ''):
        self.op_name: str = op_name
        self.try_times: int = try_times
        self.op_round: int = 0
        self.ctx: Context = ctx
        ctx.register_pause(self, self.on_pause, self.on_resume)
        self.last_screenshot: MatLike = None
        self.gc: GameConfig = game_config.get()

    def execute(self) -> bool:
        """
        循环执系列动作直到完成为止
        """
        result: bool = False
        while self.op_round < self.try_times:
            if self.ctx.running == 0:
                break
            elif self.ctx.running == 2:
                time.sleep(1)
                continue

            op_result: int = Operation.RETRY
            self.op_round += 1
            try:
                self.last_screenshot = None
                op_result = self.run()
            except Exception as e:
                op_result = Operation.RETRY
                if self.last_screenshot is not None:
                    to_save = fill_uid_black(self.last_screenshot)
                    file_name = save_debug_image(to_save, prefix=self.__class__.__name__)
                    log.error('%s执行出错 相关截图保存至 %s', self.get_display_name(), file_name, exc_info=True)
                else:
                    log.error('%s执行出错', self.get_display_name(), exc_info=True)
            if op_result == Operation.RETRY:
                continue
            elif op_result == Operation.SUCCESS:
                result = True
                break
            elif op_result == Operation.FAIL:
                result = False
                log.error('%s执行失败', self.get_display_name())
                break
            elif op_result == Operation.WAIT:
                self.op_round -= 1
                continue
            else:
                log.error('%s执行返回结果错误 %s', self.get_display_name(), result)
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

    def get_display_name(self) -> str:
        """
        用于展示的名称
        :return:
        """
        return '指令[ %s ]' % self.op_name
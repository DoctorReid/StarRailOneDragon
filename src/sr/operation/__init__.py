import time

from cv2.typing import MatLike

from basic.i18_utils import gt
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

    def __init__(self, ctx: Context, try_times: int = 2, op_name: str = '', timeout_seconds: float = -1):
        self.op_name: str = gt(op_name, 'ui')
        self.try_times: int = try_times
        self.op_round: int = 0
        self.ctx: Context = ctx
        ctx.register_pause(self, self.on_pause, self.on_resume)
        self.last_screenshot: MatLike = None
        self.gc: GameConfig = game_config.get()

        self.timeout_seconds: float = -1  # 本操作的超时时间
        self.operation_start_time: float = 0  # 开始时间
        self.pause_start_time = time.time()  # 本次暂停的开始时间
        self.pause_end_time = time.time()  # 本次暂停的结束时间
        self.pause_total_time = 0  # 暂停的总时间

    def _init_before_execute(self):
        """
        执行前的初始化
        """
        now = time.time()
        self.operation_start_time = now
        self.pause_start_time = now
        self.pause_end_time = now

    def execute(self) -> bool:
        """
        循环执系列动作直到完成为止
        """
        self._init_before_execute()
        result: bool = False
        while self.op_round < self.try_times:
            if self.timeout_seconds != -1 and self._operation_usage_time >= self.timeout_seconds:
                log.error('%s执行超时', self.display_name, exc_info=True)
                return False
            if self.ctx.running == 0:
                break
            elif self.ctx.running == 2:
                time.sleep(1)
                continue

            op_result: int = Operation.RETRY
            self.op_round += 1
            try:
                self.last_screenshot = None
                op_result = self._execute_one_round()
            except Exception as e:
                op_result = Operation.RETRY
                if self.last_screenshot is not None:
                    to_save = fill_uid_black(self.last_screenshot)
                    file_name = save_debug_image(to_save, prefix=self.__class__.__name__)
                    log.error('%s执行出错 相关截图保存至 %s', self.display_name, file_name, exc_info=True)
                else:
                    log.error('%s执行出错', self.display_name, exc_info=True)
            if op_result == Operation.RETRY:
                continue
            elif op_result == Operation.SUCCESS:
                result = True
                break
            elif op_result == Operation.FAIL:
                result = False
                if not self.allow_fail():
                    log.error('%s执行失败', self.display_name)
                break
            elif op_result == Operation.WAIT:
                self.op_round -= 1
                continue
            else:
                log.error('%s执行返回结果错误 %s', self.display_name, result)
                result = False
                break
        self.ctx.unregister(self)
        self._after_operation_done(result)
        return result

    def _execute_one_round(self) -> int:
        pass

    def on_pause(self):
        self.pause_start_time = time.time()

    def on_resume(self):
        self.pause_end_time = time.time()
        self.pause_total_time += self.pause_end_time - self.pause_start_time

    @property
    def _operation_usage_time(self) -> float:
        """
        获取指令的耗时
        :return:
        """
        return time.time() - self.operation_start_time - self.pause_start_time

    def screenshot(self):
        """
        包装一层截图 会在内存中保存上一张截图 方便出错时候保存
        :return:
        """
        self.last_screenshot = self.ctx.controller.screenshot()
        return self.last_screenshot

    @property
    def display_name(self) -> str:
        """
        用于展示的名称
        :return:
        """
        return '指令[ %s ]' % self.op_name

    def allow_fail(self) -> bool:
        """
        该指令是否允许失败
        :return:
        """
        return False

    def _after_operation_done(self, result: bool):
        """
        动作结算后的处理
        :param result:
        :return:
        """
        pass
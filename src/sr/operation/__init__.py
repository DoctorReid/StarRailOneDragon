import time
from typing import Optional, Union, ClassVar

from cv2.typing import MatLike
from pydantic import BaseModel

from basic.i18_utils import gt
from basic.img.os import save_debug_image
from basic.log_utils import log
from sr.config import game_config
from sr.config.game_config import GameConfig
from sr.context import Context
from sr.image.sceenshot import fill_uid_black


class OperationOneRoundResult(BaseModel):

    result: int
    """单轮执行结果 - 框架固定"""
    status: Optional[str] = None
    """结果附带状态 - 每个指令独特"""


class OperationResult(BaseModel):

    result: bool
    """指令执行结果 - 框架固定"""
    status: Optional[str] = None
    """结果附带状态 - 每个指令独特"""


class Operation:
    """
    基础动作
    本身可暂停 但不由自身恢复
    """
    RETRY: ClassVar[int] = 0  # 重试
    SUCCESS: ClassVar[int] = 1  # 成功
    WAIT: ClassVar[int] = 2  # 等待 本轮不计入
    FAIL: ClassVar[int] = -1  # 失败

    def __init__(self, ctx: Context, try_times: int = 2, op_name: str = '', timeout_seconds: float = -1):
        self.op_name: str = gt(op_name, 'ui')
        self.try_times: int = try_times
        self.op_round: int = 0
        self.ctx: Context = ctx
        ctx.register_pause(self, self.on_pause, self.on_resume)
        self.last_screenshot: MatLike = None
        self.gc: GameConfig = game_config.get()

        self.timeout_seconds: float = timeout_seconds  # 本操作的超时时间
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

    def execute(self) -> OperationResult:
        """
        循环执系列动作直到完成为止
        """
        self._init_before_execute()
        result: Optional[OperationResult] = Operation.op_fail('未知失败')
        while self.op_round < self.try_times:
            if self.timeout_seconds != -1 and self._operation_usage_time >= self.timeout_seconds:
                log.error('%s执行超时', self.display_name, exc_info=True)
                result = self.op_fail('执行超时')
                break
            if self.ctx.running == 0:
                result = self.op_fail('人工结束')
                break
            elif self.ctx.running == 2:
                time.sleep(1)
                continue

            round_result: Optional[OperationOneRoundResult] = None
            self.op_round += 1
            try:
                self.last_screenshot = None
                round_result = self._execute_one_round()
                if type(round_result) == OperationOneRoundResult:
                    round_result = round_result
                else:
                    round_result = OperationOneRoundResult(result=round_result, status=None)
            except Exception as e:
                round_result = self.round_retry('异常')
                if self.last_screenshot is not None:
                    to_save = fill_uid_black(self.last_screenshot)
                    file_name = save_debug_image(to_save, prefix=self.__class__.__name__)
                    log.error('%s执行出错 相关截图保存至 %s', self.display_name, file_name, exc_info=True)
                else:
                    log.error('%s执行出错', self.display_name, exc_info=True)
            if round_result.result == Operation.RETRY:
                result = Operation.op_fail(round_result.status)
                continue
            elif round_result.result == Operation.SUCCESS:
                result = self.op_success(round_result.status)
                break
            elif round_result.result == Operation.FAIL:
                result = self.op_fail(round_result.status)
                if not self.allow_fail():
                    log.error('%s执行失败', self.display_name)
                break
            elif round_result.result == Operation.WAIT:
                self.op_round -= 1
                continue
            else:
                log.error('%s执行返回结果错误 %s', self.display_name, result)
                result = self.op_fail(round_result.status)
                break
        self.ctx.unregister(self)
        self._after_operation_done(result)
        return result

    def _execute_one_round(self) -> Union[int, OperationOneRoundResult]:
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
        return time.time() - self.operation_start_time - self.pause_total_time

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

    def _after_operation_done(self, result: OperationResult):
        """
        动作结算后的处理
        :param result:
        :return:
        """
        pass

    @staticmethod
    def round_success(status: str = None) -> OperationOneRoundResult:
        """
        单轮成功 - 即整个指令成功
        :param status: 附带状态
        :return:
        """
        return OperationOneRoundResult(result=Operation.SUCCESS, status=status)

    @staticmethod
    def round_wait(status: str = None) -> OperationOneRoundResult:
        """
        单轮成功 - 即整个指令成功
        :param status: 附带状态
        :return:
        """
        return OperationOneRoundResult(result=Operation.WAIT, status=status)

    @staticmethod
    def round_retry(status: str = None) -> OperationOneRoundResult:
        """
        单轮成功 - 即整个指令成功
        :param status: 附带状态
        :return:
        """
        return OperationOneRoundResult(result=Operation.RETRY, status=status)

    @staticmethod
    def round_fail(status: str = None) -> OperationOneRoundResult:
        """
        单轮成功 - 即整个指令成功
        :param status: 附带状态
        :return:
        """
        return OperationOneRoundResult(result=Operation.FAIL, status=status)

    @staticmethod
    def op_success(status: str = None) -> OperationResult:
        """
        整个指令执行成功
        :param status: 附带状态
        :return:
        """
        return OperationResult(result=True, status=status)

    @staticmethod
    def op_fail(status: str = None) -> OperationResult:
        """
        整个指令执行成功
        :param status: 附带状态
        :return:
        """
        return OperationResult(result=False, status=status)


class OperationSuccess(Operation):
    """
    一个直接返回成功的指令 用于组合指令
    """
    def __init__(self, ctx: Context):
        super().__init__(ctx, op_name=gt('成功结束', 'ui'))

    def _execute_one_round(self) -> Union[int, OperationOneRoundResult]:
        return Operation.round_success()


class OperationFail(Operation):
    """
    一个直接返回失败的指令 用于组合指令
    """
    def __init__(self, ctx: Context):
        super().__init__(ctx, op_name=gt('成功结束', 'ui'))

    def _execute_one_round(self) -> Union[int, OperationOneRoundResult]:
        return Operation.round_fail()

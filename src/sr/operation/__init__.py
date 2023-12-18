import time
from typing import Optional, Union, ClassVar

from cv2.typing import MatLike
from pydantic import BaseModel

from basic import Rect, str_utils
from basic.i18_utils import gt, coalesce_gt
from basic.img import cv2_utils
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

    success: bool
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

    OCR_CLICK_SUCCESS: ClassVar[int] = 1  # OCR并点击成功
    OCR_CLICK_FAIL: ClassVar[int] = 0  # OCR成功但点击失败 基本不会出现
    OCR_CLICK_NOT_FOUND: ClassVar[int] = -1  # OCR找不到目标

    def __init__(self, ctx: Context, try_times: int = 2, op_name: str = '', timeout_seconds: float = -1):
        self.op_name: str = gt(op_name, 'ui')
        self.try_times: int = try_times
        self.op_round: int = 0
        self.ctx: Context = ctx
        self.last_screenshot: MatLike = None
        self.gc: GameConfig = game_config.get()

        self.timeout_seconds: float = timeout_seconds  # 本操作的超时时间
        self.operation_start_time: float = 0  # 开始时间
        self.pause_start_time = time.time()  # 本次暂停的开始时间
        self.current_pause_time = 0  # 本次暂停的总时间
        self.pause_total_time = 0  # 暂停的总时间

    def _init_before_execute(self):
        """
        执行前的初始化
        """
        now = time.time()
        self.operation_start_time = now
        self.pause_start_time = now
        self.op_round: int = 0  # 这里要做初始化 方便一个操作重复使用
        self.ctx.register_pause(self, self.on_pause, self.on_resume)

    def execute(self) -> OperationResult:
        """
        循环执系列动作直到完成为止
        """
        self._init_before_execute()
        op_result: Optional[OperationResult] = None
        retry_status: Optional[str] = None
        while self.op_round < self.try_times:
            if self.timeout_seconds != -1 and self._operation_usage_time >= self.timeout_seconds:
                log.error('%s 执行超时', self.display_name, exc_info=True)
                op_result = self.op_fail('执行超时')
                break
            if self.ctx.running == 0:
                op_result = self.op_fail('人工结束')
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
                else:  # 兼容旧版本的指令
                    round_result = OperationOneRoundResult(result=round_result, status=None)
                if self.ctx.running == 2:  # 有可能触发暂停的时候仍在执行指令 执行完成后 再次触发暂停回调 保证操作的暂停回调真正生效
                    self.on_pause()
            except Exception as e:
                round_result = self.round_retry('异常')
                if self.last_screenshot is not None:
                    to_save = fill_uid_black(self.last_screenshot)
                    file_name = save_debug_image(to_save, prefix=self.__class__.__name__)
                    log.error('%s 执行出错 相关截图保存至 %s', self.display_name, file_name, exc_info=True)
                else:
                    log.error('%s 执行出错', self.display_name, exc_info=True)
            if round_result.result == Operation.RETRY:
                retry_status = round_result.status
                continue
            elif round_result.result == Operation.SUCCESS:
                op_result = self.op_success(round_result.status)
                break
            elif round_result.result == Operation.FAIL:
                op_result = self.op_fail(round_result.status)
                break
            elif round_result.result == Operation.WAIT:
                self.op_round -= 1
                continue
            else:
                log.error('%s 执行返回结果错误 %s', self.display_name, op_result)
                op_result = self.op_fail(round_result.status)
                break

        if op_result is None:
            if self.op_round == self.try_times:  # 理论上只有重试失败的情况op_result为None
                retry_fail_status = self._retry_fail_to_success(retry_status)
                if retry_fail_status is None:
                    op_result = Operation.op_fail(retry_status)
                else:
                    op_result = Operation.op_success(retry_fail_status)
            else:
                op_result = Operation.op_fail('未知原因')

        self._after_operation_done(op_result)
        return op_result

    def _execute_one_round(self) -> Union[int, OperationOneRoundResult]:
        pass

    def on_pause(self):
        """
        暂停运行时触发的回调
        由于触发时，操作有机会仍在执行逻辑，因此_execute_one_round后会判断一次暂停状态触发on_pause
        子类需要保证多次触发不会有问题
        :return:
        """
        self.current_pause_time = 0
        self.pause_start_time = time.time()

    def on_resume(self):
        self.current_pause_time = time.time() - self.pause_start_time
        self.pause_total_time += self.current_pause_time

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

    def _retry_fail_to_success(self, retry_status: str) -> Optional[str]:
        """
        是否允许指令重试失败 返回None代表不允许
        允许情况下 重试失败会变成返回成功 而附加状态为本函数返回值
        :retry_status: 重试返回的状态
        :return:
        """
        return None

    def _after_operation_done(self, result: OperationResult):
        """
        动作结算后的处理
        :param result:
        :return:
        """
        self.ctx.unregister(self)
        if result.success:
            log.info('%s 执行成功 返回状态 %s', self.display_name, coalesce_gt(result.status, '成功', model='ui'))
        else:
            log.error('%s 执行失败 返回状态 %s', self.display_name, coalesce_gt(result.status, '失败', model='ui'))

    @staticmethod
    def round_success(status: str = None, wait: Optional[float] = None) -> OperationOneRoundResult:
        """
        单轮成功 - 即整个指令成功
        :param status: 附带状态
        :param wait: 等待秒数
        :return:
        """
        if wait is not None:
            time.sleep(wait)
        return OperationOneRoundResult(result=Operation.SUCCESS, status=status)

    @staticmethod
    def round_wait(status: str = None, wait: Optional[float] = None) -> OperationOneRoundResult:
        """
        单轮成功 - 即整个指令成功
        :param status: 附带状态
        :param wait: 等待秒数
        :return:
        """
        if wait is not None:
            time.sleep(wait)
        return OperationOneRoundResult(result=Operation.WAIT, status=status)

    @staticmethod
    def round_retry(status: str = None, wait: Optional[float] = None) -> OperationOneRoundResult:
        """
        单轮成功 - 即整个指令成功
        :param status: 附带状态
        :param wait: 等待秒数
        :return:
        """
        if wait is not None:
            time.sleep(wait)
        return OperationOneRoundResult(result=Operation.RETRY, status=status)

    @staticmethod
    def round_fail(status: str = None, wait: Optional[float] = None) -> OperationOneRoundResult:
        """
        单轮成功 - 即整个指令成功
        :param status: 附带状态
        :param wait: 等待秒数
        :return:
        """
        if wait is not None:
            time.sleep(wait)
        return OperationOneRoundResult(result=Operation.FAIL, status=status)

    @staticmethod
    def op_success(status: str = None) -> OperationResult:
        """
        整个指令执行成功
        :param status: 附带状态
        :return:
        """
        return OperationResult(success=True, status=status)

    @staticmethod
    def op_fail(status: str = None) -> OperationResult:
        """
        整个指令执行成功
        :param status: 附带状态
        :return:
        """
        return OperationResult(success=False, status=status)

    def ocr_and_click_one_line(
            self, target_cn: str,
            target_rect: Rect,
            screen: Optional[MatLike] = None,
            lcs_percent: float = 0.1,
            wait_after_success: Optional[float] = None) -> int:
        """
        对图片进行OCR找到目标文字并点击 目标区域中应该只有单行文本
        :param target_cn: 目标文本-中文
        :param target_rect: 目标文本所在的区域
        :param screen: 屏幕截图
        :param lcs_percent: 使用LCS判断OCR结果的阈值
        :param wait_after_success: 点击成功后等待的时间 取决于动画时间
        :return: 是否找到目标文本并点击
        """
        if screen is None:
            screen = self.screenshot()
        part, _ = cv2_utils.crop_image(screen, target_rect)

        ocr_result = self.ctx.ocr.ocr_for_single_line(part, strict_one_line=True)

        if str_utils.find_by_lcs(gt(target_cn, 'ocr'), ocr_result, percent=lcs_percent):
            if self.ctx.controller.click(target_rect.center):
                if wait_after_success is not None:
                    time.sleep(wait_after_success)
                return Operation.OCR_CLICK_SUCCESS
            else:
                return Operation.OCR_CLICK_FAIL

        return Operation.OCR_CLICK_NOT_FOUND


class OperationSuccess(Operation):
    """
    一个直接返回成功的指令 用于组合指令
    """
    def __init__(self, ctx: Context, status: Optional[str] = None):
        super().__init__(ctx, op_name=gt('成功结束', 'ui'))
        self.status: Optional[str] = status

    def _execute_one_round(self) -> Union[int, OperationOneRoundResult]:
        return Operation.round_success(self.status)


class OperationFail(Operation):
    """
    一个直接返回失败的指令 用于组合指令
    """
    def __init__(self, ctx: Context):
        super().__init__(ctx, op_name=gt('失败结束', 'ui'))

    def _execute_one_round(self) -> Union[int, OperationOneRoundResult]:
        return Operation.round_fail()

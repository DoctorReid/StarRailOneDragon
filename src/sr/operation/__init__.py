import time
from typing import Optional, Union, ClassVar, Callable, List, Any

from cv2.typing import MatLike

from basic import Rect, str_utils
from basic.i18_utils import gt, coalesce_gt
from basic.img import cv2_utils
from basic.img.os import save_debug_image
from basic.log_utils import log
from sr.config.game_config import GameConfig
from sr.context.context import Context, ContextEventId
from sr.image.sceenshot import fill_uid_black
from sr.screen_area import ScreenArea


class OperationOneRoundResult:

    def __init__(self, result: int, status: Optional[str] = None, data: Any = None):
        """
        指令单轮执行的结果
        :param result: 结果
        :param status: 附带状态
        """

        self.result: int = result
        """单轮执行结果 - 框架固定"""
        self.status: Optional[str] = status
        """结果状态 - 每个指令独特"""
        self.data: Any = data
        """返回数据"""

    @property
    def is_success(self) -> bool:
        return self.result == Operation.SUCCESS

    @property
    def status_display(self) -> str:
        if self.result == Operation.SUCCESS:
            return '成功'
        elif self.result == Operation.RETRY:
            return '重试'
        elif self.result == Operation.WAIT:
            return '等待'
        elif self.result == Operation.FAIL:
            return '失败'
        else:
            return '未知'


class OperationResult:

    def __init__(self, success: bool, status: Optional[str] = None, data: Any = None):
        """
        指令最后的结果
        :param success: 指令执行结果
        :param status: 附带状态
        """

        self.success: bool = success
        """指令执行结果 - 框架固定"""
        self.status: Optional[str] = status
        """结果状态 - 每个指令独特"""
        self.data: Any = data
        """返回数据"""


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

    STATUS_TIMEOUT: ClassVar[str] = '执行超时'

    def __init__(self, ctx: Context, try_times: int = 2, op_name: str = '', timeout_seconds: float = -1,
                 op_callback: Optional[Callable[[OperationResult], None]] = None):
        self.op_name: str = op_name
        """指令名称"""

        self.try_times: int = try_times
        """尝试次数"""

        self.ctx: Context = ctx
        """上下文"""

        self.last_screenshot: Optional[MatLike] = None
        """上一次的截图 用于出错时保存"""

        self.gc: GameConfig = ctx.game_config
        """游戏配置"""

        self.timeout_seconds: float = timeout_seconds
        """指令超时时间"""

        self.op_callback: Optional[Callable[[OperationResult], None]] = op_callback
        """该节点结束后的回调"""

    def _init_before_execute(self) -> Optional[OperationOneRoundResult]:
        """
        执行前的初始化
        :return:
        """
        now = time.time()

        self.op_round: int = 0
        """当前执行轮次"""

        self.operation_start_time: float = now
        """指令开始执行的时间"""

        self.pause_start_time: float = now
        """本次暂停开始的时间 on_pause时填入"""

        self.current_pause_time: float = 0
        """本次暂停的总时间 on_resume时填入"""

        self.pause_total_time: float = 0
        """暂停的总时间"""
        
        self.round_start_time: float = 0
        """本轮指令的开始时间"""

        self.ctx.event_bus.unlisten_all(self)
        self.ctx.event_bus.listen(ContextEventId.CONTEXT_PAUSE.value, self.on_pause)
        self.ctx.event_bus.listen(ContextEventId.CONTEXT_RESUME.value, self.on_resume)

        return self.handle_init()

    def handle_init(self) -> Optional[OperationOneRoundResult]:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        可以返回初始化后判断的结果
        - 成功时跳过本指令
        - 失败时立刻返回失败
        - 不返回时正常运行本指令
        """
        pass

    def execute(self) -> OperationResult:
        """
        循环执系列动作直到完成为止
        """
        init_result: OperationOneRoundResult = self._init_before_execute()
        if init_result is not None:
            if init_result.is_success:
                op_result = self.op_success(init_result.status, init_result.data)
            else:
                op_result = self.op_fail(init_result.status, init_result.data)
            self._after_operation_done(op_result)
            return op_result

        op_result: Optional[OperationResult] = None
        retry_status: Optional[str] = None
        while self.op_round < self.try_times:
            self.round_start_time = time.time()
            if self.timeout_seconds != -1 and self._operation_usage_time >= self.timeout_seconds:
                op_result = self.op_fail(Operation.STATUS_TIMEOUT)
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
                    file_name = self.save_screenshot()
                    log.error('%s 执行出错 相关截图保存至 %s', self.display_name, file_name, exc_info=True)
                else:
                    log.error('%s 执行出错', self.display_name, exc_info=True)
            if round_result.result == Operation.RETRY:
                retry_status = round_result.status
                continue
            elif round_result.result == Operation.SUCCESS:
                op_result = self.op_success(round_result.status, round_result.data)
                break
            elif round_result.result == Operation.FAIL:
                op_result = self.op_fail(round_result.status, round_result.data)
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

    def on_pause(self, e=None):
        """
        暂停运行时触发的回调
        由于触发时，操作有机会仍在执行逻辑，因此_execute_one_round后会判断一次暂停状态触发on_pause
        子类需要保证多次触发不会有问题
        :return:
        """
        if self.ctx.running != 2:
            return
        self.current_pause_time = 0
        self.pause_start_time = time.time()
        self.handle_pause()

    def handle_pause(self) -> None:
        """
        暂停后的处理 由子类实现
        :return:
        """
        pass

    def on_resume(self, e=None):
        """
        脚本恢复运行时的回调
        :param e:
        :return:
        """
        if self.ctx.running != 1:
            return
        self.current_pause_time = time.time() - self.pause_start_time
        self.pause_total_time += self.current_pause_time
        self.handle_resume()

    def handle_resume(self) -> None:
        """
        恢复运行后的处理 由子类实现
        :return:
        """
        pass

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

    def save_screenshot(self) -> str:
        """
        保存上一次的截图 并对UID打码
        :return: 文件路径
        """
        if self.last_screenshot is None:
            return ''
        fill_uid_black(self.last_screenshot)
        return save_debug_image(self.last_screenshot, prefix=self.__class__.__name__)

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
        self.ctx.event_bus.unlisten_all(self)
        if result.success:
            log.info('%s 执行成功 返回状态 %s', self.display_name, coalesce_gt(result.status, '成功', model='ui'))
        else:
            log.error('%s 执行失败 返回状态 %s', self.display_name, coalesce_gt(result.status, '失败', model='ui'))

        if self.op_callback is not None:
            self.op_callback(result)

    def round_success(self, status: str = None, data: Any = None,
                      wait: Optional[float] = None, wait_round_time: Optional[float] = None) -> OperationOneRoundResult:
        """
        单轮成功 - 即整个指令成功
        :param status: 附带状态
        :param data: 返回数据
        :param wait: 等待秒数
        :param wait_round_time: 等待当前轮的运行时间到达这个时间时再结束 有wait时不生效
        :return:
        """
        self._after_round_wait(wait=wait, wait_round_time=wait_round_time)
        return OperationOneRoundResult(result=Operation.SUCCESS, status=status, data=data)

    def round_wait(self, status: str = None, data: Any = None,
                   wait: Optional[float] = None, wait_round_time: Optional[float] = None) -> OperationOneRoundResult:
        """
        单轮成功 - 即整个指令成功
        :param status: 附带状态
        :param data: 返回数据
        :param wait: 等待秒数
        :param wait_round_time: 等待当前轮的运行时间到达这个时间时再结束 有wait时不生效
        :return:
        """
        self._after_round_wait(wait=wait, wait_round_time=wait_round_time)
        return OperationOneRoundResult(result=Operation.WAIT, status=status, data=data)

    def round_retry(self, status: str = None, data: Any = None,
                    wait: Optional[float] = None, wait_round_time: Optional[float] = None) -> OperationOneRoundResult:
        """
        单轮成功 - 即整个指令成功
        :param status: 附带状态
        :param data: 返回数据
        :param wait: 等待秒数
        :param wait_round_time: 等待当前轮的运行时间到达这个时间时再结束 有wait时不生效
        :return:
        """
        self._after_round_wait(wait=wait, wait_round_time=wait_round_time)
        return OperationOneRoundResult(result=Operation.RETRY, status=status, data=data)

    def round_fail(self, status: str = None, data: Any = None,
                   wait: Optional[float] = None, wait_round_time: Optional[float] = None) -> OperationOneRoundResult:
        """
        单轮成功 - 即整个指令成功
        :param status: 附带状态
        :param data: 返回数据
        :param wait: 等待秒数
        :param wait_round_time: 等待当前轮的运行时间到达这个时间时再结束 有wait时不生效
        :return:
        """
        self._after_round_wait(wait=wait, wait_round_time=wait_round_time)
        return OperationOneRoundResult(result=Operation.FAIL, status=status, data=data)

    def _after_round_wait(self, wait: Optional[float] = None, wait_round_time: Optional[float] = None):
        """
        每轮指令后进行的等待
        :param wait: 等待秒数
        :param wait_round_time: 等待当前轮的运行时间到达这个时间时再结束 有wait时不生效
        :return:
        """
        if wait is not None and wait > 0:
            time.sleep(wait)
        elif wait_round_time is not None and wait_round_time > 0:
            to_wait = wait_round_time - (time.time() - self.round_start_time)
            if to_wait > 0:
                time.sleep(to_wait)

    @staticmethod
    def op_success(status: str = None, data: Any = None) -> OperationResult:
        """
        整个指令执行成功
        :param status: 附带状态
        :param data: 返回数据
        :return:
        """
        return OperationResult(success=True, status=status, data=data)

    @staticmethod
    def op_fail(status: str = None, data: Any = None) -> OperationResult:
        """
        整个指令执行失败
        :param status: 附带状态
        :param data: 返回数据
        :return:
        """
        return OperationResult(success=False, status=status, data=data)

    def round_by_op(self, op_result: OperationResult, retry_on_fail: bool = False,
                    wait: Optional[float] = None, wait_round_time: Optional[float] = None) -> OperationOneRoundResult:
        """
        根据一个指令的结果获取当前轮的结果
        :param op_result: 指令结果
        :param retry_on_fail: 失败的时候是否重试
        :param wait: 等待时间
        :param wait_round_time: 等待当前轮的运行时间到达这个时间时再结束 有wait时不生效
        :return:
        """
        if op_result.success:
            return self.round_success(status=op_result.status, data=op_result.data, wait=wait, wait_round_time=wait_round_time)
        elif retry_on_fail:
            return self.round_retry(status=op_result.status, data=op_result.data, wait=wait, wait_round_time=wait_round_time)
        else:
            return self.round_fail(status=op_result.status, data=op_result.data, wait=wait, wait_round_time=wait_round_time)

    def round_fail_by_op(self, op_result: OperationResult) -> OperationOneRoundResult:
        return self.round_fail(status=op_result.status, data=op_result.data)

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

    def find_and_click_area(self, area: ScreenArea, screen: Optional[MatLike] = None) -> int:
        """
        在一个区域匹配成功后进行点击
        :param area: 目标区域
        :param screen: 屏幕截图
        :return:
        """
        if screen is None:
            screen = self.screenshot()
        if area.text is not None:
            rect = area.rect
            part = cv2_utils.crop_image_only(screen, rect)

            ocr_result = self.ctx.ocr.ocr_for_single_line(part, strict_one_line=True)

            if str_utils.find_by_lcs(gt(area.text, 'ocr'), ocr_result, percent=area.lcs_percent):
                if self.ctx.controller.click(rect.center, pc_alt=area.pc_alt):
                    return Operation.OCR_CLICK_SUCCESS
                else:
                    return Operation.OCR_CLICK_FAIL

            return Operation.OCR_CLICK_NOT_FOUND
        elif area.template_id is not None:
            rect = area.rect
            part = cv2_utils.crop_image_only(screen, rect)

            mrl = self.ctx.im.match_template(part, area.template_id,
                                             template_sub_dir=area.template_sub_dir,
                                             threshold=area.template_match_threshold)
            if mrl.max is None:
                return Operation.OCR_CLICK_NOT_FOUND
            elif self.ctx.controller.click(mrl.max.center + rect.left_top, pc_alt=area.pc_alt):
                return Operation.OCR_CLICK_SUCCESS
            else:
                return Operation.OCR_CLICK_FAIL
        else:
            return Operation.OCR_CLICK_FAIL

    def round_by_find_and_click_area(self, screen: MatLike, area: ScreenArea,
                                     success_wait: Optional[float] = None, success_wait_round: Optional[float] = None,
                                     retry_wait: Optional[float] = None, retry_wait_round: Optional[float] = None,
                                     ) -> OperationOneRoundResult:
        """
        是否能找到目标区域 并进行点击
        :param screen: 屏幕截图
        :param area: 目标区域
        :param success_wait: 成功后等待的秒数
        :param success_wait_round: 成功后等待当前轮的运行时间到达这个时间时再结束 优先success_wait
        :param retry_wait: 失败后等待的秒数
        :param retry_wait_round: 失败后等待当前轮的运行时间到达这个时间时再结束 优先success_wait
        :return:
        """
        click = self.find_and_click_area(area=area, screen=screen)
        if click == Operation.OCR_CLICK_SUCCESS:
            return self.round_success(status=area.status, wait=success_wait, wait_round_time=success_wait_round)
        elif click == Operation.OCR_CLICK_NOT_FOUND:
            return self.round_retry(status=f'未找到{area.status}',wait=retry_wait, wait_round_time=retry_wait_round)
        elif click == Operation.OCR_CLICK_FAIL:
            return self.round_retry(status=f'点击{area.status}失败', wait=retry_wait, wait_round_time=retry_wait_round)
        else:
            return self.round_retry(status='未知状态', wait=retry_wait, wait_round_time=retry_wait_round)

    def find_area(self, area: ScreenArea, screen: Optional[MatLike] = None) -> bool:
        """
        在一个区域匹配成功后进行点击
        :param area: 目标区域
        :param screen: 屏幕截图
        :return:
        """
        if screen is None:
            screen = self.screenshot()
        if area.text is not None:
            rect = area.rect
            part = cv2_utils.crop_image_only(screen, rect)

            ocr_result = self.ctx.ocr.ocr_for_single_line(part, strict_one_line=True)

            return str_utils.find_by_lcs(gt(area.text, 'ocr'), ocr_result, percent=area.lcs_percent)
        elif area.template_id is not None:
            rect = area.rect
            part = cv2_utils.crop_image_only(screen, rect)

            mrl = self.ctx.im.match_template(part, area.template_id, threshold=area.template_match_threshold)
            return mrl.max is not None
        else:
            return False

    def round_by_find_area(self, screen: MatLike, area: ScreenArea,
                           success_wait: Optional[float] = None, success_wait_round: Optional[float] = None,
                           retry_wait: Optional[float] = None, retry_wait_round: Optional[float] = None,
                           ) -> OperationOneRoundResult:
        """
        是否能找到目标区域
        :param screen: 屏幕截图
        :param area: 目标区域
        :param success_wait: 成功后等待的秒数
        :param success_wait_round: 成功后等待当前轮的运行时间到达这个时间时再结束 优先success_wait
        :param retry_wait: 失败后等待的秒数
        :param retry_wait_round: 失败后等待当前轮的运行时间到达这个时间时再结束 优先success_wait
        :return:
        """
        if self.find_area(area=area, screen=screen):
            return self.round_success(wait=success_wait, wait_round_time=success_wait_round)
        else:
            return self.round_retry(wait=retry_wait, wait_round_time=retry_wait_round)



class OperationSuccess(Operation):
    """
    一个直接返回成功的指令 用于组合指令
    """
    def __init__(self, ctx: Context, status: Optional[str] = None, data: Any = None,
                 op_callback: Optional[Callable[[OperationResult], None]] = None
                 ):
        super().__init__(ctx, op_name=gt('成功结束', 'ui'), op_callback=op_callback)
        self.status: Optional[str] = status
        self.data: Any = data

    def _execute_one_round(self) -> Union[int, OperationOneRoundResult]:
        return self.round_success(status=self.status, data=self.data)


class OperationFail(Operation):
    """
    一个直接返回失败的指令 用于组合指令
    """
    def __init__(self, ctx: Context, status: Optional[str] = None):
        super().__init__(ctx, op_name=gt('失败结束', 'ui'))
        self.status: Optional[str] = status

    def _execute_one_round(self) -> Union[int, OperationOneRoundResult]:
        return self.round_fail(status=self.status)


class StateOperationNode:

    def __init__(self, cn: str,
                 func: Optional[Callable[[], OperationOneRoundResult]] = None,
                 op: Optional[Operation] = None,
                 retry_on_op_fail: bool = False,
                 wait_after_op: Optional[float] = None,
                 timeout_seconds: Optional[float] = None):
        """
        带状态指令的节点
        :param cn: 节点名称
        :param func: 该节点用于处理指令的函数 与op只传一个 优先使用func
        :param op: 该节点用于操作的指令 与func只传一个 优先使用func
        :param retry_on_op_fail: op指令失败时是否进入重试
        :param wait_after_op: op指令后的等待时间
        :param timeout_seconds: 该节点的超时秒数
        """

        self.cn: str = cn
        """节点名称"""

        self.func: Callable[[], OperationOneRoundResult] = func
        """节点处理函数"""

        self.op: Optional[Operation] = op
        """节点操作指令"""

        self.retry_on_op_fail: bool = retry_on_op_fail
        """op指令失败时是否进入重试"""

        self.wait_after_op: Optional[float] = wait_after_op
        """op指令后的等待时间"""

        self.timeout_seconds: Optional[float] = timeout_seconds
        """该节点的超时秒数"""


class StateOperationEdge:

    def __init__(self, node_from: StateOperationNode, node_to: StateOperationNode,
                 success: bool = True, status: Optional[str] = None, ignore_status: bool = True):
        """
        带状态指令的边
        :param node_from: 上一个指令
        :param node_to: 下一个指令
        :param success: 是否成功才进入下一个节点
        :param status: 上一个节点的结束状态 符合时才进入下一个节点
        :param ignore_status: 是否忽略状态进行下一个节点 不会忽略success
        """

        self.node_from: StateOperationNode = node_from
        """上一个节点"""

        self.node_to: StateOperationNode = node_to
        """下一个节点"""

        self.success: bool = success
        """是否成功才执行下一个节点"""

        self.status: Optional[str] = status
        """
        执行下一个节点的条件状态 
        一定要完全一样才会执行 包括None
        """

        self.ignore_status: bool = False if status is not None else ignore_status
        """
        是否忽略状态进行下一个节点
        一个节点应该最多只有一条边忽略返回状态
        忽略返回状态只有在所有需要匹配的状态都匹配不到时才会用做兜底
        """


class StateOperation(Operation):

    def __init__(self, ctx: Context, op_name: str, try_times: int = 3,
                 nodes: Optional[List[StateOperationNode]] = None,
                 edges: Optional[List[StateOperationEdge]] = None,
                 specified_start_node: Optional[StateOperationNode] = None,
                 timeout_seconds: float = -1,
                 op_callback: Optional[Callable[[OperationResult], None]] = None):
        """
        带有状态的指令
        :param ctx: 上下文
        :param op_name: 指令名称
        :param try_times: 重试次数，所有节点共享
        :param nodes: 指令的节点 与edges至少传入一个。只传入nodes认为按顺序执行
        :param edges: 指令的边 与nodes至少传入一个。传入edges时，忽略传入的nodes。根据edges构建执行的网图
        :param specified_start_node: 指定的开始节点。当网图有环时候使用，指定后脚本不会根据网图入度自动判断开始节点。
        :param op_callback: 指令的回调
        """
        Operation.__init__(self, ctx, op_name=op_name, try_times=try_times, timeout_seconds=timeout_seconds, op_callback=op_callback)

        self.param_edge_list: List[StateOperationEdge] = edges
        """入参的边列表"""

        self.param_node_list: List[StateOperationNode] = nodes
        """入参的节点列表"""

        self.param_start_node: StateOperationNode = specified_start_node
        """入参的开始节点 当网络存在环时 需要自己指定"""

        self.add_edge_list: List[StateOperationEdge] = []
        """调用方法添加的边"""

    def add_edges_and_nodes(self) -> None:
        """
        初始化前 添加边和节点 由子类实行
        :return:
        """
        pass

    def _init_edge_list(self) -> None:
        """
        初始化边列表
        :return:
        """
        self.edge_list: List[StateOperationEdge] = []
        """合并的边列表"""

        if self.param_edge_list is not None:
            for edge in self.param_edge_list:
                self.edge_list.append(edge)
        if len(self.add_edge_list) > 0:
            for edge in self.add_edge_list:
                self.edge_list.append(edge)

        if len(self.edge_list) == 0 and self.param_node_list is not None:
            if len(self.param_node_list) == 1:
                self.param_start_node = self.param_node_list[0]
            else:
                last_node = None
                for node in self.param_node_list:
                    if last_node is not None:
                        self.edge_list.append(StateOperationEdge(last_node, node))
                    last_node = node

    def add_edge(self, node_from: StateOperationNode, node_to: StateOperationNode,
                 success: bool = True, status: Optional[str] = None, ignore_status: bool = True):
        """
        添加一条边
        :param node_from:
        :param node_to:
        :param success:
        :param status:
        :param ignore_status:
        :return:
        """
        self.add_edge_list.append(StateOperationEdge(node_from, node_to,
                                                     success=success, status=status, ignore_status=ignore_status))

    def _init_network(self) -> None:
        """
        进行节点网络的初始化
        :return:
        """
        self.add_edges_and_nodes()
        self._init_edge_list()

        self._node_edges_map: dict[str, List[StateOperationEdge]] = {}
        """下一个节点的集合"""

        self._node_map: dict[str, StateOperationNode] = {}
        """节点"""

        self._current_node_start_time: Optional[float] = None
        """当前节点的开始运行时间"""

        self._multiple_start: bool = False
        """是否有多个开始节点 有的话属于异常情况"""

        op_in_map: dict[str, int] = {}  # 入度

        for edge in self.edge_list:
            from_id = edge.node_from.cn
            if from_id not in self._node_edges_map:
                self._node_edges_map[from_id] = []
            self._node_edges_map[from_id].append(edge)

            to_id = edge.node_to.cn
            if to_id not in op_in_map:
                op_in_map[to_id] = 0
            op_in_map[to_id] = op_in_map[to_id] + 1

            self._node_map[from_id] = edge.node_from
            self._node_map[to_id] = edge.node_to

        start_node: Optional[StateOperationNode] = None
        if self.param_start_node is None:  # 没有指定开始节点时 自动判断
            # 找出入度为0的开始点
            for edge in self.edge_list:
                from_id = edge.node_from.cn
                if from_id not in op_in_map or op_in_map[from_id] == 0:
                    if start_node is not None and start_node.cn != from_id:
                        start_node = None
                        break
                    start_node = self._node_map[from_id]
        else:
            start_node = self.param_start_node

        self._start_node: StateOperationNode = start_node
        """其实节点 初始化后才会有"""

        self._current_node: StateOperationNode = start_node
        """当前执行的节点"""

    def _init_before_execute(self) -> Optional[OperationOneRoundResult]:
        """
        执行前的初始化 注意初始化要全面 方便一个指令重复使用
        可以返回初始化后判断的结果
        - 成功时跳过本指令
        - 失败时立刻返回失败
        - 不返回时正常运行本指令
        """
        init_result = super()._init_before_execute()
        if init_result is not None:
            return init_result

        self._init_network()
        self._current_node_start_time = time.time()

        if self._start_node is None:
            return self.round_fail('未定义开始节点')
        else:
            return None

    def _execute_one_round(self) -> OperationOneRoundResult:
        if self._current_node is None:
            return self.round_fail('无开始节点')

        if self._current_node.timeout_seconds is not None \
                and self._current_node_start_time is not None \
                and time.time() - self._current_node_start_time > self._current_node.timeout_seconds:
            return self.round_fail(Operation.STATUS_TIMEOUT)

        if self._current_node.func is not None:
            current_op = self._current_node.func
            current_round_result: OperationOneRoundResult = current_op()
            if self._current_node.wait_after_op is not None:
                time.sleep(self._current_node.wait_after_op)
        elif self._current_node.op is not None:
            op_result = self._current_node.op.execute()
            current_round_result = self.round_by_op(op_result,
                                                    retry_on_fail=self._current_node.retry_on_op_fail,
                                                    wait=self._current_node.wait_after_op)
        else:
            return self.round_fail('节点处理函数和指令都没有设置')

        if current_round_result is None:
            log.error(f'节点 {self._current_node.cn} 返回状态为None')

        # 重试到足够次数了 这里设置成失败
        # 因为有可能失败还有下一个节点 如果返回重试 则会返回整个op的失败
        if current_round_result.result == Operation.RETRY and self.op_round + 1 >= self.try_times:
            current_round_result.result = Operation.FAIL

        log.info('%s 节点 %s 返回状态 %s', self.display_name, self._current_node.cn,
                 coalesce_gt(current_round_result.status, current_round_result.status_display, model='ui'))

        if current_round_result.result == Operation.WAIT or current_round_result.result == Operation.RETRY:
            # 等待或重试的 直接返回
            return current_round_result

        edges = self._node_edges_map.get(self._current_node.cn)
        if edges is None:  # 没有下一个节点了 已经结束了 当前返回就是什么
            return current_round_result

        next_node_id: Optional[str] = None
        final_next_node_id: Optional[str] = None  # 兜底指令
        for edge in edges:
            if edge.success != (current_round_result.result == Operation.SUCCESS):
                continue

            if edge.ignore_status:
                final_next_node_id = edge.node_to.cn

            if edge.status is None and current_round_result.status is None:
                next_node_id = edge.node_to.cn
                break
            elif edge.status is None or current_round_result.status is None:
                continue
            elif edge.status == current_round_result.status:
                next_node_id = edge.node_to.cn
                break

        next_node: Optional[StateOperationNode] = None
        if next_node_id is not None:
            next_node = self._node_map[next_node_id]
        elif final_next_node_id is not None:
            next_node = self._node_map[final_next_node_id]

        if next_node is None:  # 没有下一个节点了 已经结束了
            return current_round_result

        self._current_node = next_node
        self.op_round = 0  # 重置 每个节点都可以重试
        self._current_node_start_time = time.time()  # 每个节点单独计算耗时
        return self.round_wait()

    def on_resume(self, e=None):
        super().on_resume(e)
        if self._current_node_start_time is not None:
            self._current_node_start_time += self.current_pause_time

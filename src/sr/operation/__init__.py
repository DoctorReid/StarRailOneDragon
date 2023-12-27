import time
from typing import Optional, Union, ClassVar, Callable, List

from cv2.typing import MatLike

from basic import Rect, str_utils
from basic.i18_utils import gt, coalesce_gt
from basic.img import cv2_utils
from basic.img.os import save_debug_image
from basic.log_utils import log
from sr.config import game_config
from sr.config.game_config import GameConfig
from sr.context import Context
from sr.image.sceenshot import fill_uid_black


class OperationOneRoundResult:

    def __init__(self, result: int, status: Optional[str] = None):
        """
        指令单轮执行的结果
        :param result: 结果
        :param status: 附带状态
        """

        self.result: int = result
        """单轮执行结果 - 框架固定"""
        self.status: Optional[str] = status
        """结果附带状态 - 每个指令独特"""


class OperationResult:

    def __init__(self, success: bool, status: Optional[str] = None):
        """
        指令最后的结果
        :param success: 指令执行结果
        :param status: 附带状态
        """

        self.success: bool = success
        """指令执行结果 - 框架固定"""
        self.status: Optional[str] = status
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

    def __init__(self, ctx: Context, try_times: int = 2, op_name: str = '', timeout_seconds: float = -1,
                 op_callback: Optional[Callable[[OperationResult], None]] = None):
        self.op_name: str = op_name
        """指令名称"""

        self.try_times: int = try_times
        """尝试次数"""

        self.op_round: int = 0
        """当前执行轮次"""

        self.ctx: Context = ctx
        """上下文"""

        self.last_screenshot: Optional[MatLike] = None
        """上一次的截图 用于出错时保存"""

        self.gc: GameConfig = game_config.get()
        """游戏配置"""

        self.timeout_seconds: float = timeout_seconds
        """指令超时时间"""

        self.operation_start_time: float = 0
        """指令开始执行的时间"""

        self.pause_start_time: float = 0
        """本次暂停开始的时间 on_pause时填入"""

        self.current_pause_time: float = 0
        """本次暂停的总时间 on_resume时填入"""

        self.pause_total_time: float = 0
        """暂停的总时间"""

        self.executing: bool = False
        """是否正在执行 用于判断能否进行初始化 暂停时也算是在执行"""

        self.op_callback: Optional[Callable[[OperationResult], None]] = op_callback
        """该节点结束后的回调"""

    def _init_before_execute(self):
        """
        执行前的初始化 注意初始化要全面 方便一个指令重复使用
        """
        now = time.time()
        self.operation_start_time = now
        self.pause_start_time = now
        self.current_pause_time = 0
        self.pause_total_time = 0
        self.op_round = 0
        self.executing = True
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
        self.executing = False
        if result.success:
            log.info('%s 执行成功 返回状态 %s', self.display_name, coalesce_gt(result.status, '成功', model='ui'))
        else:
            log.error('%s 执行失败 返回状态 %s', self.display_name, coalesce_gt(result.status, '失败', model='ui'))

        if self.op_callback is not None:
            self.op_callback(result)

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
        整个指令执行失败
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


class StateOperationNode:

    def __init__(self, cn: str, func: Callable[[], OperationOneRoundResult]):
        """
        带状态指令的节点
        :param cn: 节点名称
        :param func: 该节点用于处理指令的函数
        """

        self.cn: str = cn
        """节点名称"""

        self.func: Callable[[], OperationOneRoundResult] = func
        """节点处理函数"""


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

    def __init__(self, ctx: Context, op_name: str, try_times: int = 2,
                 nodes: Optional[List[StateOperationNode]] = None,
                 edges: Optional[List[StateOperationEdge]] = None,
                 specified_start_node: Optional[StateOperationNode] = None):
        """
        带有状态的指令
        :param ctx: 上下文
        :param op_name: 指令名称
        :param try_times: 重试次数，所有节点共享
        :param nodes: 指令的节点 与edges至少传入一个。只传入nodes认为按顺序执行
        :param edges: 指令的边 与nodes至少传入一个。传入edges时，忽略传入的nodes。根据edges构建执行的网图
        :param specified_start_node: 指定的开始节点。当网图有环时候使用，指定后脚本不会根据网图入度自动判断开始节点。
        """
        super().__init__(ctx, op_name=op_name, try_times=try_times)

        self.edge_list: List[StateOperationEdge] = []
        """边列表"""

        self._node_edges_map: dict[str, List[StateOperationEdge]] = {}
        """下一个节点的集合"""

        self._node_map: dict[str, StateOperationNode] = {}
        """节点"""

        self._specified_start_node: Optional[StateOperationNode] = specified_start_node
        """指定的开始节点 当网络存在环时 需要自己指定"""

        self._start_node: Optional[StateOperationNode] = None
        """其实节点 初始化后才会有"""

        self._multiple_start: bool = False
        """是否有多个开始节点 属于异常情况"""

        self._current_node: Optional[StateOperationNode] = None
        """当前执行的节点"""

        if edges is not None:
            for edge in edges:
                self.register_edge(edge)
        elif nodes is not None:
            pass

    def register_edge(self, edge: StateOperationEdge):
        """
        注册一条边
        :param edge:
        :return:
        """
        if self.executing:
            log.error('%s 正在执行 无法进行节点注册', self.display_name)
            return
        self.edge_list.append(edge)

    def set_specified_start_node(self, start_node: StateOperationNode):
        """
        设置开始节点
        :param start_node: 开始节点
        :return:
        """
        if self.executing:
            log.error('%s 正在执行 无法设置开始节点', self.display_name)
            return
        self._specified_start_node = start_node

    def _init_network(self):
        """
        进行节点网络的初始化
        :return:
        """
        self._node_edges_map = {}
        self._node_map = {}
        self._start_node = None
        self._multiple_start = False

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

        if self._specified_start_node is None:  # 没有指定开始节点时 自动判断
            # 找出入度为0的开始点
            for edge in self.edge_list:
                from_id = edge.node_from.cn
                if from_id not in op_in_map or op_in_map[from_id] == 0:
                    if self._start_node is not None and self._start_node.cn != from_id:
                        self._start_node = None
                        break
                    self._start_node = self._node_map[from_id]
        else:
            self._start_node = self._specified_start_node

    def _init_before_execute(self):
        """
        执行前的初始化 注意初始化要全面 方便一个指令重复使用
        """
        super()._init_before_execute()
        self._init_network()
        self._current_node = self._start_node

    def _execute_one_round(self) -> OperationOneRoundResult:
        if self._current_node is None:
            return Operation.round_fail('无开始节点')
        current_op = self._current_node.func
        current_round_result: OperationOneRoundResult = current_op()

        edges = self._node_edges_map.get(self._current_node.cn)
        if edges is None:  # 没有下一个节点了 已经结束了
            return Operation.round_success()
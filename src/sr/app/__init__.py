from datetime import datetime
from typing import List, Optional

from basic import os_utils
from basic.log_utils import log
from sr.config import game_config, ConfigHolder
from sr.const import game_config_const
from sr.context import Context
from sr.operation import Operation, OperationResult
from sr.operation.combine import StatusCombineOperation2, StatusCombineOperationEdge2, StatusCombineOperationNode
from sr.operation.unit.enter_game import EnterGame


class AppRunRecord(ConfigHolder):

    STATUS_WAIT = 0
    STATUS_SUCCESS = 1
    STATUS_FAIL = 2
    STATUS_RUNNING = 3

    def __init__(self, app_id: str):
        self.dt: str = ''
        self.run_time: str = ''
        self.run_status: int = AppRunRecord.STATUS_WAIT  # 0=未运行 1=成功 2=失败 3=运行中
        super().__init__(app_id, sub_dir=['app_run_record'], sample=False)

    def _init_after_read_file(self):
        self.dt = self.get('dt', app_record_current_dt_str())
        self.run_time = self.get('run_time', '-')
        self.run_status = self.get('run_status', AppRunRecord.STATUS_WAIT)

    def check_and_update_status(self):
        """
        检查并更新状态 各个app按需实现
        :return:
        """
        if self._should_reset_by_dt():
            self.reset_record()

    def update_status(self, new_status: int, only_status: bool = False):
        """
        更新状态
        :param new_status:
        :param only_status: 是否只更新状态
        :return:
        """
        self.run_status = new_status
        self.update('run_status', self.run_status, False)
        if not only_status:
            self.dt = app_record_current_dt_str()
            self.run_time = app_record_now_time_str()
            self.update('dt', self.dt, False)
            self.update('run_time', self.run_time, False)

        self.save()

    def reset_record(self):
        """
        运行记录重置 非公共部分由各app自行实现
        :return:
        """
        self.update_status(AppRunRecord.STATUS_WAIT, only_status=True)

    @property
    def run_status_under_now(self):
        """
        基于当前时间显示的运行状态
        :return:
        """
        if self._should_reset_by_dt():
            return AppRunRecord.STATUS_WAIT
        else:
            return self.run_status

    def _should_reset_by_dt(self) -> bool:
        """
        根据时间判断是否应该重置状态
        :return:
        """
        current_dt = app_record_current_dt_str()
        return self.dt != current_dt


class Application(Operation):

    def __init__(self, ctx: Context, op_name: str = None,
                 init_context_before_start: bool = True,
                 stop_context_after_stop: bool = True,
                 run_record: Optional[AppRunRecord] = None):
        super().__init__(ctx, try_times=1,  # 应用只是组装指令 不应该有重试
                         op_name=op_name,
                         )

        self.run_record: Optional[AppRunRecord] = run_record
        """运行记录"""

        self.init_context_before_start: bool = init_context_before_start
        """运行前是否初始化上下文 一条龙只有第一个应用需要"""

        self.stop_context_after_stop: bool = stop_context_after_stop
        """运行后是否停止上下文 一条龙只有最后一个应用需要"""

    def _init_context(self) -> bool:
        """
        上下文的初始化
        :return: 是否初始化成功
        """
        if not self.init_context_before_start:
            return True

        if not self.ctx.start_running():
            return False

        if self.ctx.open_game_by_script:
            op = EnterGame(self.ctx)
            result = op.execute()
            if not result.success:
                log.error('进入游戏失败')
                self.ctx.stop_running()
                return False

        return True

    def execute(self) -> OperationResult:
        if not self._init_context():
            return Operation.op_fail('初始化失败')
        result: OperationResult = super().execute()
        self._stop_context()
        return result

    def on_resume(self):
        super().on_resume()
        self.ctx.controller.init()

    def _stop_context(self):
        if self.stop_context_after_stop:
            self.ctx.stop_running()

    def _after_operation_done(self, result: OperationResult):
        """
        停止后的处理
        :return:
        """
        Operation._after_operation_done(self, result)
        if self.run_record is not None:
            if result.success:
                self.run_record.update_status(AppRunRecord.STATUS_SUCCESS)
            else:
                self.run_record.update_status(AppRunRecord.STATUS_FAIL)

    @property
    def current_execution_desc(self) -> str:
        """
        当前运行的描述 用于UI展示
        :return:
        """
        return ''

    @property
    def next_execution_desc(self) -> str:
        """
        下一步运行的描述 用于UI展示
        :return:
        """
        return ''


class Application2(StatusCombineOperation2):

    def __init__(self, ctx: Context, op_name: str = None,
                 edges: Optional[List[StatusCombineOperationEdge2]] = None,
                 specified_start_node: Optional[StatusCombineOperationNode] = None,
                 init_context_before_start: bool = True,
                 stop_context_after_stop: bool = True,
                 run_record: Optional[AppRunRecord] = None):
        StatusCombineOperation2.__init__(self, ctx, op_name=op_name,
                                         edges=edges, specified_start_node=specified_start_node)

        self.run_record: Optional[AppRunRecord] = run_record
        """运行记录"""

        self.init_context_before_start: bool = init_context_before_start
        """运行前是否初始化上下文 一条龙只有第一个应用需要"""

        self.stop_context_after_stop: bool = stop_context_after_stop
        """运行后是否停止上下文 一条龙只有最后一个应用需要"""

    def _init_context(self) -> bool:
        """
        上下文的初始化
        :return: 是否初始化成功
        """
        if not self.init_context_before_start:
            return True

        if not self.ctx.start_running():
            return False

        if self.ctx.open_game_by_script:
            op = EnterGame(self.ctx)
            result = op.execute()
            if not result.success:
                log.error('进入游戏失败')
                self.ctx.stop_running()
                return False

        return True

    def _init_before_execute(self):
        StatusCombineOperation2._init_before_execute(self)
        self.run_record.update_status(AppRunRecord.STATUS_RUNNING)

    def execute(self) -> OperationResult:
        if not self._init_context():
            return Operation.op_fail('初始化失败')
        result: OperationResult = StatusCombineOperation2.execute(self)
        return result

    def on_resume(self):
        StatusCombineOperation2.on_resume(self)
        self.ctx.controller.init()

    def _stop_context(self):
        if self.stop_context_after_stop:
            self.ctx.stop_running()

    def _after_operation_done(self, result: OperationResult):
        """
        停止后的处理
        :return:
        """
        StatusCombineOperation2._after_operation_done(self, result)
        self._update_record_stop(result)
        self._stop_context()

    def _update_record_stop(self, result: OperationResult):
        """
        应用停止后的对运行记录的更新
        :param result: 运行结果
        :return:
        """
        if self.run_record is not None:
            if result.success:
                self.run_record.update_status(AppRunRecord.STATUS_SUCCESS)
            else:
                self.run_record.update_status(AppRunRecord.STATUS_FAIL)

    @property
    def current_execution_desc(self) -> str:
        """
        当前运行的描述 用于UI展示
        :return:
        """
        return ''

    @property
    def next_execution_desc(self) -> str:
        """
        下一步运行的描述 用于UI展示
        :return:
        """
        return ''


def app_record_now_time_str() -> str:
    """
    返回当前时间字符串
    :return: 例如 11-13 10:11
    """
    current_time = datetime.now()
    return current_time.strftime("%m-%d %H:%M")


def app_record_current_dt_str() -> str:
    """
    游戏区服当前的日期
    :return:
    """
    sr = game_config.get().server_region
    utc_offset = game_config_const.SERVER_TIME_OFFSET.get(sr)
    return os_utils.get_dt(utc_offset)


class AppDescription:

    def __init__(self, cn: str, id: str):
        self.cn: str = cn
        self.id: str = id


ALL_APP_LIST: List[AppDescription] = [
]


def register_app(app_desc: AppDescription):
    """
    注册app 注册后才能在一条龙上看到
    :param app_desc:
    :return:
    """
    ALL_APP_LIST.append(app_desc)


def get_app_desc_by_id(app_id: str) -> Optional[AppDescription]:
    for app in ALL_APP_LIST:
        if app.id == app_id:
            return app
    return None

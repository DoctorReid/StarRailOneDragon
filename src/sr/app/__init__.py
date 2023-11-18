from datetime import datetime
from typing import List, Optional

from basic import os_utils
from basic.log_utils import log
from sr.config import game_config, ConfigHolder
from sr.const import game_config_const
from sr.context import Context
from sr.operation import Operation
from sr.operation.unit.enter_game import EnterGame


class Application(Operation):

    def __init__(self, ctx: Context, op_name: str = None,
                 init_context_before_start: bool = True,
                 stop_context_after_stop: bool = True,):
        super().__init__(ctx, op_name=op_name)
        self.init_context_before_start: bool = init_context_before_start
        self.stop_context_after_stop: bool = stop_context_after_stop

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
            if not op.execute():
                log.error('进入游戏失败')
                self.ctx.stop_running()
                return False

        return True

    def execute(self) -> bool:
        if not self._init_context():
            return False
        result: bool = super().execute()
        self._stop_context()
        self._after_stop(result)
        return result

    def on_resume(self):
        super().on_resume()
        self.ctx.controller.init()

    def _stop_context(self):
        if self.stop_context_after_stop:
            self.ctx.stop_running()

    def _after_stop(self, result: bool):
        """
        停止后的处理
        :return:
        """
        pass

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
        self._reset_if_another_dt()

    def _reset_if_another_dt(self):
        """
        如果已经到新的一天了 重置状态
        由app自己控制什么时候重置
        :return:
        """
        current_dt = app_record_current_dt_str()
        if self.dt != current_dt:
            self.run_status = AppRunRecord.STATUS_WAIT
            self._reset_for_new_dt()

    def update_status(self, new_status: int):
        self.dt = app_record_current_dt_str()
        self.run_status = new_status
        self.run_time = app_record_now_time_str()
        self.update('dt', self.dt, False)
        self.update('run_status', self.run_status, False)
        self.update('run_time', self.run_time, False)

        self.save()

    def _reset_for_new_dt(self):
        """
        运行记录重试 非公共部分由各app自行实现
        :return:
        """
        pass

    @property
    def run_status_under_now(self):
        """
        基于当前时间显示的运行状态
        :return:
        """
        current_dt = app_record_current_dt_str()
        if self.dt != current_dt:
            return AppRunRecord.STATUS_WAIT
        else:
            return self.run_status


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

import time
from datetime import datetime
from typing import Optional

from basic import os_utils
from basic.config import ConfigHolder
from sr.const import game_config_const


class AppRunRecord(ConfigHolder):

    STATUS_WAIT = 0
    STATUS_SUCCESS = 1
    STATUS_FAIL = 2
    STATUS_RUNNING = 3

    def __init__(self, app_id: str,
                 account_idx: Optional[int] = None,
                 server_region: str = game_config_const.SERVER_REGION_CN):
        self.server_region: str = server_region  # 游戏对应的服务器
        self.dt: str = ''
        self.run_time: str = ''
        self.run_time_float: float = 0
        self.run_status: int = AppRunRecord.STATUS_WAIT  # 0=未运行 1=成功 2=失败 3=运行中
        super().__init__(app_id, account_idx=account_idx, sub_dir=['app_run_record'], sample=False)

    def _init_after_read_file(self):
        self.dt = self.get('dt', self.get_current_dt())
        self.run_time = self.get('run_time', '-')
        self.run_time_float = self.get('run_time_float', 0)
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
            self.dt = self.get_current_dt()
            self.run_time = self.app_record_now_time_str()
            self.run_time_float = time.time()
            self.update('dt', self.dt, False)
            self.update('run_time', self.run_time, False)
            self.update('run_time_float', self.run_time_float, False)

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
        current_dt = self.get_current_dt()
        return self.dt != current_dt

    def get_current_dt(self) -> str:
        """
        获取当前时间的dt
        :return:
        """
        utc_offset = game_config_const.SERVER_TIME_OFFSET.get(self.server_region)
        return os_utils.get_dt(utc_offset)

    @staticmethod
    def app_record_now_time_str() -> str:
        """
        返回当前时间字符串
        :return: 例如 11-13 10:11
        """
        current_time = datetime.now()
        return current_time.strftime("%m-%d %H:%M")

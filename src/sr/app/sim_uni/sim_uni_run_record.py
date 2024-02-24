from typing import Optional

from basic import os_utils
from sr.app.app_description import AppDescriptionEnum
from sr.app.app_run_record import AppRunRecord
from sr.app.sim_uni.sim_uni_config import SimUniConfig


class SimUniRunRecord(AppRunRecord):

    def __init__(self, config: SimUniConfig, account_idx: Optional[int] = None):
        super().__init__(AppDescriptionEnum.SIM_UNIVERSE.value.id, account_idx=account_idx)
        self.config = config

    @property
    def run_status_under_now(self):
        """
        基于当前时间显示的运行状态
        :return:
        """
        if self._should_reset_by_dt():
            if os_utils.is_monday(self.get_current_dt()):
                return AppRunRecord.STATUS_WAIT
            elif self.weekly_times >= self.config.weekly_times:  # 已完成本周次数
                return AppRunRecord.STATUS_SUCCESS
            else:
                return AppRunRecord.STATUS_WAIT
        else:
            if self.daily_times >= self.config.daily_times:  # 已完成本日次数
                return AppRunRecord.STATUS_SUCCESS
            else:
                return AppRunRecord.STATUS_WAIT

    def reset_record(self):
        """
        运行记录重置 非公共部分由各app自行实现
        :return:
        """
        super().reset_record()
        current_dt = self.get_current_dt()
        if os_utils.get_money_dt(current_dt) != os_utils.get_money_dt(self.dt):
            self.weekly_times = 0
        self.daily_times = 0

    def add_times(self):
        """
        增加一次完成次数
        :return:
        """
        self.daily_times = self.daily_times + 1
        self.weekly_times = self.weekly_times + 1

    @property
    def weekly_times(self) -> int:
        """
        每周挑战的次数
        :return:
        """
        return self.get('weekly_times', 0)

    @weekly_times.setter
    def weekly_times(self, new_value: int):
        self.update('weekly_times', new_value)

    @property
    def daily_times(self) -> int:
        """
        每天挑战的次数
        :return:
        """
        return self.get('daily_times', 0)

    @daily_times.setter
    def daily_times(self, new_value: int):
        self.update('daily_times', new_value)

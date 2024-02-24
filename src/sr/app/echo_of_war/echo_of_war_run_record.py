from typing import Optional

from basic import os_utils
from sr.app.app_description import AppDescriptionEnum
from sr.app.app_run_record import AppRunRecord


class EchoOfWarRunRecord(AppRunRecord):

    def __init__(self, account_idx: Optional[int] = None):
        super().__init__(AppDescriptionEnum.ECHO_OF_WAR.value.id, account_idx=account_idx)

    def _should_reset_by_dt(self) -> bool:
        """
        根据时间判断是否应该重置状态 每周重置一次
        :return:
        """
        current_dt = self.get_current_dt()
        sunday_dt = os_utils.get_sunday_dt(self.dt)
        return current_dt > sunday_dt

    def reset_record(self):
        """
        运行记录重置 非公共部分由各app自行实现
        :return:
        """
        super().reset_record()
        self.left_times = 3

    @property
    def run_status_under_now(self):
        """
        基于当前时间显示的运行状态
        :return:
        """
        current_dt = self.get_current_dt()
        sunday_dt = os_utils.get_sunday_dt(self.dt)
        if current_dt > sunday_dt:
            return AppRunRecord.STATUS_WAIT
        else:
            return self.run_status

    @property
    def left_times(self) -> int:
        return self.get('left_times', 3)

    @left_times.setter
    def left_times(self, new_value: int):
        self.update('left_times', new_value)


echo_of_war_record: Optional[EchoOfWarRunRecord] = None


def get_record() -> EchoOfWarRunRecord:
    global echo_of_war_record
    if echo_of_war_record is None:
        echo_of_war_record = EchoOfWarRunRecord()
    return echo_of_war_record

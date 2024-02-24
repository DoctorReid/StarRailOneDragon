from typing import Optional

from basic import os_utils
from sr.app.app_description import AppDescriptionEnum
from sr.app.app_run_record import AppRunRecord


class BuyXianZhouParcelRunRecord(AppRunRecord):

    def __init__(self, account_idx: Optional[int] = None):
        super().__init__(AppDescriptionEnum.BUY_XIANZHOU_PARCEL.value.id, account_idx=account_idx)

    def _should_reset_by_dt(self) -> bool:
        """
        根据时间判断是否应该重置状态 每周重置一次
        :return:
        """
        current_dt = self.get_current_dt()
        sunday_dt = os_utils.get_sunday_dt(self.dt)
        return current_dt > sunday_dt

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

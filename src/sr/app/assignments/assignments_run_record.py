import time
from typing import Optional

from sr.app.app_description import AppDescriptionEnum
from sr.app.app_run_record import AppRunRecord
from sr.mystools import mys_config


class AssignmentsRunRecord(AppRunRecord):

    def __init__(self, account_idx: Optional[int] = None):
        super().__init__(AppDescriptionEnum.ASSIGNMENTS.value.id, account_idx=account_idx)

    def check_and_update_status(self):
        """
        检查并更新状态 各个app按需实现
        :return:
        """
        if self._should_reset_by_dt() or self.claim_dt < self.get_current_dt():
            self.reset_record()

    def _should_reset_by_dt(self):
        """
        根据米游社便签更新
        有任何一个委托可以接受
        :return:
        """
        if super()._should_reset_by_dt():
            return True
        config = mys_config.get()

        if self.claim_dt >= self.get_current_dt() or self.run_time_float > config.refresh_time:
            return False

        if config.refresh_time > 0:
            now = time.time()
            usage_time = now - config.refresh_time
            e_arr = config.expeditions
            for e in e_arr:
                if e.remaining_time - usage_time <= 0:
                    return True
        return False

    @property
    def claim_dt(self) -> str:
        """
        领取委托奖励的日期
        :return:
        """
        return self.get('claim_dt', '20240101')

    @claim_dt.setter
    def claim_dt(self, new_value: str):
        """
        领取委托奖励的日期
        :return:
        """
        self.update('claim_dt', new_value)

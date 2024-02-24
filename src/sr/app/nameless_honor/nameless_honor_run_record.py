from typing import Optional

from sr.app.app_description import AppDescriptionEnum
from sr.app.app_run_record import AppRunRecord


class NamelessHonorRunRecord(AppRunRecord):

    def __init__(self, account_idx: Optional[int] = None):
        super().__init__(AppDescriptionEnum.NAMELESS_HONOR.value.id, account_idx=account_idx)

    def _should_reset_by_dt(self) -> bool:
        """
        根据时间判断是否应该重置状态
        :return: 总是尝试
        """
        return True

from typing import Optional

from sr.app.app_description import AppDescriptionEnum
from sr.app.app_run_record import AppRunRecord


class TrickSnackRunRecord(AppRunRecord):

    def __init__(self, account_idx: Optional[int] = None):
        super().__init__(AppDescriptionEnum.TRICK_SNACK.value.id, account_idx=account_idx)

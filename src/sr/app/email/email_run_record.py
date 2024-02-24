from typing import Optional

from sr.app.app_description import AppDescriptionEnum
from sr.app.app_run_record import AppRunRecord


class EmailRecord(AppRunRecord):

    def __init__(self, account_idx: Optional[int] = None):
        super().__init__(AppDescriptionEnum.EMAIL.value.id, account_idx=account_idx)


email_record: Optional[EmailRecord] = None


def get_record() -> EmailRecord:
    global email_record
    if email_record is None:
        email_record = EmailRecord()
    return email_record

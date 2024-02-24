from typing import Optional

from sr.app.app_description import AppDescriptionEnum
from sr.app.app_run_record import AppRunRecord


class SupportCharacterRunRecord(AppRunRecord):

    def __init__(self, account_idx: Optional[int] = None):
        super().__init__(AppDescriptionEnum.SUPPORT_CHARACTER.value.id, account_idx=account_idx)


support_character_record: Optional[SupportCharacterRunRecord] = None


def get_record() -> SupportCharacterRunRecord:
    global support_character_record
    if support_character_record is None:
        support_character_record = SupportCharacterRunRecord()
    return support_character_record

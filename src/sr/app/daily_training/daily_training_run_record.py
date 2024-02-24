from typing import Optional

from sr.app.app_description import AppDescriptionEnum
from sr.app.app_run_record import AppRunRecord


class DailyTrainingRunRecord(AppRunRecord):

    def __init__(self, account_idx: Optional[int] = None):
        super().__init__(AppDescriptionEnum.DAILY_TRAINING.value.id, account_idx=account_idx)

    def reset_record(self):
        """
        运行记录重置 非公共部分由各app自行实现
        :return:
        """
        super().reset_record()
        self.score = 0

    @property
    def score(self) -> int:
        return self.get('score', 0)

    @score.setter
    def score(self, new_value: int):
        self.update('score', new_value)


_daily_training_record: Optional[DailyTrainingRunRecord] = None


def get_record() -> DailyTrainingRunRecord:
    global _daily_training_record
    if _daily_training_record is None:
        _daily_training_record = DailyTrainingRunRecord()
    return _daily_training_record

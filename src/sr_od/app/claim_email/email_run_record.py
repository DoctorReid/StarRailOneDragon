from typing import Optional

from one_dragon.base.operation.application_run_record import AppRunRecord


class EmailRunRecord(AppRunRecord):

    def __init__(self, instance_idx: Optional[int] = None):
        AppRunRecord.__init__(self, 'email', instance_idx=instance_idx)

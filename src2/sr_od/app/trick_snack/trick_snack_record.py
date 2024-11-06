from typing import Optional

from one_dragon.base.operation.application_run_record import AppRunRecord


class TrickSnackRunRecord(AppRunRecord):

    def __init__(self, instance_idx: Optional[int] = None):
        AppRunRecord.__init__(self, 'trick_snack', instance_idx=instance_idx)

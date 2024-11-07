from typing import Optional

from one_dragon.base.operation.application_run_record import AppRunRecord, AppRunRecordPeriod


class BuyXianZhouParcelRunRecord(AppRunRecord):

    def __init__(self, instance_idx: Optional[int] = None):
        AppRunRecord.__init__(self, 'buy_xianzhou_parcel', instance_idx=instance_idx,
                              record_period=AppRunRecordPeriod.WEEKLY)

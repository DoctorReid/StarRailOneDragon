import time
from typing import Optional

from sr.app.app_run_record import AppRunRecord
from sr.app.app_description import AppDescriptionEnum
from sr.app.trailblaze_power.trailblaze_power_config import TrailblazePowerConfig
from sr.mystools import mys_config
from sr.interastral_peace_guide.survival_index_mission import SurvivalIndexMission, SurvivalIndexMissionEnum


class TrailblazePowerRunRecord(AppRunRecord):

    def __init__(self, tp_config: TrailblazePowerConfig, account_idx: Optional[int] = None):
        self.tp_config: TrailblazePowerConfig = tp_config
        super().__init__(AppDescriptionEnum.TRAILBLAZE_POWER.value.id, account_idx=account_idx)

    def _should_reset_by_dt(self):
        """
        根据米游社便签判断是否有足够体力进行下一次副本
        :return:
        """
        mys = mys_config.get()
        now = time.time()
        time_usage = now - mys.refresh_time
        power = mys.current_stamina + time_usage // 360  # 6分钟恢复一点体力
        if self.tp_config.next_plan_item is not None:
            point: Optional[SurvivalIndexMission] = SurvivalIndexMissionEnum.get_by_unique_id(self.tp_config.next_plan_item['mission_id'])
            return point is not None and power >= point.power
        return False


trailblaze_power_record: Optional[TrailblazePowerRunRecord] = None


def get_record() -> TrailblazePowerRunRecord:
    global trailblaze_power_record
    if trailblaze_power_record is None:
        trailblaze_power_record = TrailblazePowerRunRecord()
    return trailblaze_power_record

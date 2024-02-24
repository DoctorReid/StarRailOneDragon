from typing import List, Optional

import numpy as np

from sr.app import AppRunRecord
from sr.app.app_description import AppDescriptionEnum
from sr.app.world_patrol.world_patrol_route import WorldPatrolRouteId


class WorldPatrolRunRecord(AppRunRecord):

    def __init__(self, account_idx: Optional[int] = None):
        self.finished: List[str] = []
        self.time_cost: dict[str, List] = {}
        super().__init__(AppDescriptionEnum.WORLD_PATROL.value.id,
                         account_idx=account_idx)

    def _init_after_read_file(self):
        super()._init_after_read_file()
        self.finished = self.get('finished', [])
        self.time_cost = self.get('time_cost', {})

    def reset_record(self):
        super().reset_record()
        self.finished = []

        self.update('finished', self.finished, False)

        self.save()

    def add_record(self, route_id: WorldPatrolRouteId, time_cost):
        unique_id = route_id.unique_id
        self.finished.append(unique_id)
        if unique_id not in self.time_cost:
            self.time_cost[unique_id] = []
        self.time_cost[unique_id].append(time_cost)
        while len(self.time_cost[unique_id]) > 3:
            self.time_cost[unique_id].pop(0)

        self.update('run_time', self.app_record_now_time_str(), False)
        self.update('dt', self.dt, False)
        self.update('finished', self.finished, False)
        self.update('time_cost', self.time_cost, False)
        self.save()

    def get_estimate_time(self, route_id: WorldPatrolRouteId):
        unique_id = route_id.unique_id
        if unique_id not in self.time_cost:
            return 0
        else:
            return np.mean(self.time_cost[unique_id])

import threading
import time
from typing import List, Iterator

from basic.log_utils import log
from sr.app import Application, AppRunRecord
from sr.app.world_patrol import WorldPatrolRouteId, WorldPatrolWhitelist, WorldPatrolRecord, \
    load_all_route_id, get_record
from sr.app.world_patrol.run_patrol_route import RunPatrolRoute
from sr.config import game_config
from sr.context import Context
from sr.image.sceenshot import mini_map_angle_alas
from sr.operation import Operation


class WorldPatrol(Application):

    def __init__(self, ctx: Context, whitelist: WorldPatrolWhitelist = None,
                 ignore_record: bool = False):
        super().__init__(ctx)
        self.route_id_list: List[WorldPatrolRouteId] = []
        self.first: bool = True
        self.record: WorldPatrolRecord = None
        self.route_iterator: Iterator = None
        self.whitelist: WorldPatrolWhitelist = whitelist
        self.current_route_idx: int = -1
        self.ignore_record: bool = ignore_record
        self.current_route_start_time = time.time()  # 当前路线开始时间

    def _init_before_execute(self):
        if not self.ignore_record:
            self.record = get_record()
            self.record.reset_if_another_dt()
            self.record.update_status(AppRunRecord.STATUS_RUNNING)

        self.route_id_list = load_all_route_id(self.whitelist, None if self.record is None else self.record.finished)

        self.current_route_idx = -1

        t = threading.Thread(target=self.preheat)
        t.start()

    def preheat(self):
        """
        预热
        - 提前加载需要的模板
        - 角度匹配用的矩阵
        :return:
        """
        self.ctx.ih.preheat_for_world_patrol()
        mm_r = game_config.get().mini_map_pos.r
        for i in range(-2, 2):
            mini_map_angle_alas.RotationRemapData((mm_r + i) * 2)

    def _execute_one_round(self) -> int:
        self.current_route_idx += 1
        if self.current_route_idx >= len(self.route_id_list):
            log.info('所有线路执行完毕')
            return Operation.SUCCESS

        route_id = self.route_id_list[self.current_route_idx]

        self.current_route_start_time = time.time()
        op = RunPatrolRoute(self.ctx, route_id, self.first)
        route_result = op.execute()
        if route_result:
            self.first = False
            if not self.ignore_record:
                self.save_record(route_id, time.time() - self.current_route_start_time)

        return Operation.WAIT

    def save_record(self, route_id: WorldPatrolRouteId, time_cost: float):
        """
        保存当天运行记录
        :param route_id: 路线ID
        :param time_cost: 使用时间
        :return:
        """
        self.record.add_record(route_id, time_cost)

    def estimate_end_time(self):
        """
        剩余路线预估的完成时间
        :return:
        """
        total = - (time.time() - self.current_route_start_time)
        for i in range(self.current_route_idx, len(self.route_id_list)):
            total += self.record.get_estimate_time(self.route_id_list[i])

            if total < 0:  # 只有第一条，也就是当前线路时会为负
                total = 0

        return total

    def _after_stop(self, result: bool):
        if result and len(self.route_id_list) >= len(self.record.finished):
            self.record.result = AppRunRecord.STATUS_SUCCESS
        else:
            self.record.result = AppRunRecord.STATUS_FAIL

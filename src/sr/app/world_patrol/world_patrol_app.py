import threading
import time
from typing import List, Iterator, Optional

import sr.app.world_patrol.world_patrol_run_record
from basic.i18_utils import gt
from basic.log_utils import log
from sr.app.app_run_record import AppRunRecord
from sr.app.application_base import Application
from sr.app.world_patrol.world_patrol_config import WorldPatrolConfig
from sr.app.world_patrol.world_patrol_route import WorldPatrolRouteId, WorldPatrolWhitelist, load_all_route_id, \
    load_all_whitelist_id
from sr.app.world_patrol.world_patrol_run_record import WorldPatrolRunRecord
from sr.app.world_patrol.world_patrol_run_route import WorldPatrolRunRoute
from sr.context import Context
from sr.image.sceenshot import mini_map_angle_alas
from sr.operation import Operation, OperationResult
from sr.operation.combine.choose_team_in_world import ChooseTeamInWorld


class WorldPatrol(Application):

    def __init__(self, ctx: Context,
                 whitelist: Optional[WorldPatrolWhitelist] = None,
                 ignore_record: bool = False,
                 team_num: Optional[int] = None):
        super().__init__(ctx, op_name=gt('锄大地', 'ui'),
                         run_record=ctx.world_patrol_run_record)
        self.route_id_list: List[WorldPatrolRouteId] = []
        self.record: WorldPatrolRunRecord = None
        self.route_iterator: Iterator = None
        self.current_route_idx: int = -1
        self.ignore_record: bool = ignore_record
        self.current_route_start_time = time.time()  # 当前路线开始时间

        self.config: WorldPatrolConfig = ctx.world_patrol_config
        self.team_num: Optional[int] = team_num
        if whitelist is None:
            valid_whitelist_id_list = load_all_whitelist_id()
            if self.config.whitelist_id in valid_whitelist_id_list:
                whitelist = WorldPatrolWhitelist(self.config.whitelist_id)
        self.whitelist: WorldPatrolWhitelist = whitelist

    def _init_before_execute(self):
        if not self.ignore_record:
            self.record = self.ctx.world_patrol_run_record
            self.record.update_status(AppRunRecord.STATUS_RUNNING)

        self.route_id_list = load_all_route_id(self.whitelist, None if self.record is None else self.record.finished)

        self.current_route_idx = -1

        if self.team_num is None:
            self.team_num = self.config.team_num

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
        mm_r = self.ctx.game_config.mini_map_pos.r
        for i in range(-2, 2):
            mini_map_angle_alas.RotationRemapData((mm_r + i) * 2)

    def _execute_one_round(self) -> int:
        self.current_route_idx += 1
        if self.current_route_idx >= len(self.route_id_list):
            log.info('所有线路执行完毕')
            return Operation.SUCCESS

        if self.current_route_idx == 0 and self.team_num != 0:
            op = ChooseTeamInWorld(self.ctx, self.config.team_num)
            if not op.execute().success:
                return Operation.FAIL

        route_id = self.route_id_list[self.current_route_idx]

        self.current_route_start_time = time.time()
        op = WorldPatrolRunRoute(self.ctx, route_id, technique_fight=self.config.technique_fight)
        route_result = op.execute().success
        if route_result:
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

    def _after_operation_done(self, result: OperationResult):
        Operation._after_operation_done(self, result)
        if self.ignore_record:
            return
        if not result.success:
            self.record.update_status(AppRunRecord.STATUS_FAIL)
            return

        for route_id in self.route_id_list:
            if route_id.unique_id not in self.record.finished:
                self.record.update_status(AppRunRecord.STATUS_FAIL)
                return

        self.record.update_status(AppRunRecord.STATUS_SUCCESS)

    @property
    def current_execution_desc(self) -> str:
        """
        当前运行的描述 用于UI展示
        :return:
        """
        return gt('锄大地', 'ui')

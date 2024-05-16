import time
from typing import List, Optional, ClassVar

from basic.i18_utils import gt
from sr.app.app_run_record import AppRunRecord
from sr.app.application_base import Application
from sr.app.world_patrol.world_patrol_config import WorldPatrolConfig
from sr.app.world_patrol.world_patrol_route import WorldPatrolRouteId, load_all_route_id
from sr.app.world_patrol.world_patrol_run_route import WorldPatrolRunRoute
from sr.app.world_patrol.world_patrol_whitelist_config import WorldPatrolWhitelist, load_all_whitelist_id
from sr.context import Context
from sr.image.sceenshot import mini_map
from sr.operation import Operation, OperationResult, StateOperationEdge, StateOperationNode, OperationOneRoundResult
from sr.operation.common.back_to_normal_world_plus import BackToNormalWorldPlus
from sr.operation.common.cancel_mission_trace import CancelMissionTrace
from sr.operation.unit.team import SwitchMember, ChooseTeamInWorld


class WorldPatrol(Application):

    STATUS_ALL_ROUTE_FINISHED: ClassVar[str] = '所有路线已完成'

    def __init__(self, ctx: Context,
                 whitelist: Optional[WorldPatrolWhitelist] = None,
                 ignore_record: bool = False,
                 team_num: Optional[int] = None):
        edges: List[StateOperationEdge] = []

        world = StateOperationNode('返回大世界', op=BackToNormalWorldPlus(ctx))
        cancel_trace = StateOperationNode('取消任务追踪', op=CancelMissionTrace(ctx))
        edges.append(StateOperationEdge(world, cancel_trace))

        team = StateOperationNode('选择配队', self._choose_team)
        edges.append(StateOperationEdge(cancel_trace, team))

        switch = StateOperationNode('切换1号位', op=SwitchMember(ctx, 1))
        edges.append(StateOperationEdge(team, switch))

        route = StateOperationNode('运行路线', self._run_route)
        edges.append(StateOperationEdge(switch, route, ignore_status=True))
        edges.append(StateOperationEdge(route, route, ignore_status=False))

        super().__init__(ctx, op_name=gt('锄大地', 'ui'),
                         run_record=ctx.world_patrol_run_record if not ignore_record else None,
                         edges=edges
                         )
        self.route_id_list: List[WorldPatrolRouteId] = []
        self.current_route_idx: int = 0
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
        super()._init_before_execute()

        self.route_id_list = load_all_route_id(self.whitelist,
                                               None if self.ignore_record else self.ctx.world_patrol_run_record.finished)

        self.current_route_idx = 0

        Application.get_preheat_executor().submit(self.preheat)

    def preheat(self):
        """
        预热
        - 提前加载需要的模板
        - 角度匹配用的矩阵
        :return:
        """
        self.ctx.ih.preheat_for_world_patrol()
        mini_map.preheat()

    def _choose_team(self) -> OperationOneRoundResult:
        """
        选择配队
        :return:
        """
        team_num = self.ctx.world_patrol_config.team_num if self.team_num is None else self.team_num
        if team_num == 0:
            return Operation.round_success('无配队配置')
        op = ChooseTeamInWorld(self.ctx, team_num)
        return Operation.round_by_op(op.execute())

    def _run_route(self):
        if self.current_route_idx >= len(self.route_id_list):
            return Operation.round_success(WorldPatrol.STATUS_ALL_ROUTE_FINISHED)
        route_id = self.route_id_list[self.current_route_idx]

        self.current_route_start_time = time.time()
        op = WorldPatrolRunRoute(self.ctx, route_id)
        route_result = op.execute().success
        if route_result:
            if not self.ignore_record:
                self.save_record(route_id, time.time() - self.current_route_start_time)

        self.current_route_idx += 1
        return Operation.round_success()

    def save_record(self, route_id: WorldPatrolRouteId, time_cost: float):
        """
        保存当天运行记录
        :param route_id: 路线ID
        :param time_cost: 使用时间
        :return:
        """
        self.ctx.world_patrol_run_record.add_record(route_id, time_cost)

    def estimate_end_time(self):
        """
        剩余路线预估的完成时间
        :return:
        """
        total = - (time.time() - self.current_route_start_time)
        for i in range(self.current_route_idx, len(self.route_id_list)):
            total += self.ctx.world_patrol_run_record.get_estimate_time(self.route_id_list[i])

            if total < 0:  # 只有第一条，也就是当前线路时会为负
                total = 0

        return total

    def _update_record_after_stop(self, result: OperationResult):
        if self.ignore_record:
            return
        if not result.success:
            self.ctx.world_patrol_run_record.update_status(AppRunRecord.STATUS_FAIL)
            return

        for route_id in self.route_id_list:
            if route_id.unique_id not in self.ctx.world_patrol_run_record.finished:
                self.ctx.world_patrol_run_record.update_status(AppRunRecord.STATUS_FAIL)
                return

        self.ctx.world_patrol_run_record.update_status(AppRunRecord.STATUS_SUCCESS)

    @property
    def current_execution_desc(self) -> str:
        """
        当前运行的描述 用于UI展示
        :return:
        """
        return gt('锄大地', 'ui')

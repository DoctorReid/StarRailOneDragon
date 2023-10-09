import os
from typing import List

from basic import os_utils
from basic.log_utils import log
from sr import constants
from sr.config import ConfigHolder
from sr.constants.map import TransportPoint, region_with_another_floor
from sr.context import Context
from sr.operation import Operation
from sr.operation.combine.transport import Transport
from sr.operation.unit.move_directly import MoveDirectly


class WorldPatrolRoute(ConfigHolder):

    def __init__(self, route_id: str):
        self.tp: TransportPoint = None
        self.route_list: List = None
        super().__init__(route_id, sample=False, sub_dir='world_patrol')

    def init(self):
        self.init_from_data(**self.data)

    def init_from_data(self, planet: str, region: str, tp: str, level: int, route: List):
        self.tp: TransportPoint = constants.map.get_tp_by_cn(planet, region, level, tp)
        self.route_list = route


class WorldPatrolRecord(ConfigHolder):

    def __init__(self, current_dt: str, restart: bool = False):
        self.restart = restart
        self.current_dt: str = current_dt
        self.dt: str = None
        self.finished: List = None
        super().__init__('record', sample=False, sub_dir='world_patrol')

    def init(self):
        if self.data is not None:
            self.dt = self.data['dt']
            self.finished = self.data['finished']

        if self.restart or (self.dt is not None and self.dt < self.current_dt) or self.dt is None:  # 重新开始
            self.dt = self.current_dt
            self.finished = []

    def save(self):
        self.update('dt', self.dt)
        self.update('finished', self.finished)
        self.write_config()


class WorldPatrol(Operation):

    def __init__(self, ctx: Context, restart: bool = False):
        super().__init__(ctx)
        self.route_list = []

        dir = os_utils.get_path_under_work_dir('config', 'world_patrol')
        for filename in os.listdir(dir):
            if filename == 'record.yml':
                continue
            idx = filename.find('.yml')
            if idx == -1:
                continue
            self.route_list.append(filename[0:idx])

        log.info('共加载 %d 条线路', len(self.route_list))

        self.record = WorldPatrolRecord(os_utils.get_dt(), restart=restart)
        log.info('之前已完成线路 %d 条', len(self.record.finished))
        self.first: bool = True

        self.route_iterator = iter(self.route_list)

    def run(self) -> int:
        try:
            route_id = next(self.route_iterator)
        except StopIteration:
            log.info('所有线路执行完毕')
            return Operation.SUCCESS

        self.run_one_route(route_id)
        self.first = False

        return Operation.WAIT

    def run_one_route(self, route_id):
        route: WorldPatrolRoute = WorldPatrolRoute(route_id)
        log.info('准备执行线路 %s %s %s %s', route_id, route.tp.planet.cn, route.tp.region.cn, route.tp.cn)
        if route_id in self.record.finished:
            log.info('线路 %s 之前已执行 跳过', route_id)
            return

        log.info('准备传送 %s %s %s', route.tp.planet.cn, route.tp.region.cn, route.tp.cn)
        op = Transport(self.ctx, route.tp, self.first)
        if not op.execute():
            log.error('传送失败 即将跳过本次路线 %s', route_id)
            return
        else:
            log.info('传送完成 开始寻路')

        last_region = route.tp.region
        lm = self.ctx.ih.get_large_map(last_region, map_type='origin')
        lm_info = self.ctx.map_cal.analyse_large_map(lm)
        last_pos = route.tp.lm_pos
        for p in route.route_list:
            target_pos = (p[0], p[1])
            op = MoveDirectly(self.ctx, lm_info, target=target_pos, start=last_pos)
            if not op.execute():
                log.error('寻路失败 出发点 %s 目标点 %s 即将跳过本次路线 %s', route_id)
                return

            if len(p) > 2:  # 需要切换层数
                last_region = region_with_another_floor(last_region, p[2])
                lm = self.ctx.ih.get_large_map(last_region, map_type='origin')
                lm_info = self.ctx.map_cal.analyse_large_map(lm)

            last_pos = target_pos

        self.save_record(route_id)

    def save_record(self, route_id):
        """
        保存当天运行记录
        :param route_id: 路线ID
        :return:
        """
        self.record.finished.append(route_id)
        self.record.save()
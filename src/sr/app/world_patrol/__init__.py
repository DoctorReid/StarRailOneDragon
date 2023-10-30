import os
from typing import List

import numpy as np

from basic import os_utils
from basic.i18_utils import gt
from basic.log_utils import log
from sr.config import ConfigHolder
from sr.const import map_const
from sr.const.map_const import Planet, Region, TransportPoint, PLANET_2_REGION, REGION_2_SP, PLANET_LIST


class WorldPatrolRouteId:

    def __init__(self, planet: Planet, raw_id: str):
        idx = -1
        idx_cnt = 0
        while True:
            idx = raw_id.find('_', idx + 1)
            if idx == -1:
                break
            idx_cnt += 1
        idx = raw_id.rfind('_')

        self.route_num: int = 0 if idx_cnt == 3 else int(raw_id[idx+1:])

        self.planet: Planet = planet
        self.region: Region = None
        self.tp: TransportPoint = None

        for region in PLANET_2_REGION.get(planet.np_id):
            if raw_id.startswith(region.r_id):
                self.region: Region = region
                break

        for sp in REGION_2_SP.get(self.region.pr_id):
            if self.route_num == 0:
                if raw_id.endswith(sp.id):
                    self.tp = sp
                    break
            else:
                if raw_id[:raw_id.rfind('_')].endswith(sp.id):
                    self.tp = sp
                    break

        assert self.tp is not None

        self.raw_id = raw_id

    @property
    def display_name(self):
        """
        用于前端显示路线名称
        :return:
        """
        return '%s_%s_%s' % (gt(self.planet.cn, 'ui'), gt(self.region.cn, 'ui'), gt(self.tp.cn, 'ui')) + ('' if self.route_num == 0 else '_%02d' % self.route_num)

    @property
    def unique_id(self):
        """
        唯一标识 用于各种配置中保存
        :return:
        """
        return '%s_%s_%s' % (self.planet.np_id, self.region.r_id, self.tp.id) + ('' if self.route_num == 0 else '_%02d' % self.route_num)

    def equals(self, another_route_id):
        return another_route_id is not None and self.planet == another_route_id.planet and self.raw_id == another_route_id.raw_id

    @property
    def file_path(self):
        """
        对应的文件路径
        :return:
        """
        dir_path = os_utils.get_path_under_work_dir('config', 'world_patrol', self.planet.np_id)
        return os.path.join(dir_path, '%s.yml' % self.raw_id)


class WorldPatrolRoute(ConfigHolder):

    def __init__(self, route_id: WorldPatrolRouteId):
        self.author_list: List[str] = None
        self.tp: TransportPoint = None
        self.route_list: List = None
        self.route_id: WorldPatrolRouteId = route_id
        super().__init__(route_id.raw_id, sample=False, sub_dir=['world_patrol', route_id.planet.np_id])

    def init(self):
        self.init_from_data(**self.data)

    def init_from_data(self, author: List[str], planet: str, region: str, tp: str, floor: int, route: List):
        self.author_list = author
        self.tp: TransportPoint = map_const.get_sp_by_cn(planet, region, floor, tp)
        self.route_list = route

    @property
    def display_name(self):
        return self.route_id.display_name

class WorldPatrolWhitelist(ConfigHolder):

    def __init__(self, file_name: str):
        self.id: str = file_name
        self.type: str = None
        self.list: List[str] = []
        super().__init__(file_name, sample=False, sub_dir=['world_patrol', 'whitelist'])

    def init(self):
        if self.data is not None:
            self.type = self.data['type']
            self.list = self.data['list']

    @property
    def valid(self) -> bool:
        return self.type in ['white', 'black'] and len(self.list) > 0


class WorldPatrolRecord(ConfigHolder):

    def __init__(self, current_dt: str, restart: bool = False):
        self.restart = restart
        self.current_dt: str = current_dt
        self.dt: str = current_dt
        self.finished: List[str] = []
        self.time_cost: dict[str, List] = {}
        super().__init__('record', sample=False, sub_dir=['world_patrol'])

    def init(self):
        if self.data is not None:
            self.dt = self.data['dt']
            self.finished = self.data['finished']
            self.time_cost = self.data['time_cost']

        if self.restart or (self.dt is not None and self.dt != self.current_dt) or self.dt is None:  # 重新开始、新的一天、无记录
            self.dt = self.current_dt
            self.finished = []

    def add_record(self, route_id: WorldPatrolRouteId, time_cost):
        unique_id = route_id.unique_id
        self.finished.append(unique_id)
        if unique_id not in self.time_cost:
            self.time_cost[unique_id] = []
        self.time_cost[unique_id].append(time_cost)
        while len(self.time_cost[unique_id]) > 3:
            self.time_cost[unique_id].pop(0)

        self.update('dt', self.dt)
        self.update('finished', self.finished)
        self.update('time_cost', self.time_cost)
        self.write_config()

    def get_estimate_time(self, route_id: WorldPatrolRouteId):
        unique_id = route_id.unique_id
        if unique_id not in self.time_cost:
            return 0
        else:
            return np.mean(self.time_cost[unique_id])


def load_all_route_id(whitelist: WorldPatrolWhitelist = None, finished: List[WorldPatrolRouteId] = None) -> List[WorldPatrolRouteId]:
    """
    加载所有路线
    :param whitelist: 白名单
    :param finished: 已完成的列表
    :return:
    """
    route_id_arr: List[WorldPatrolRouteId] = []
    dir_path = os_utils.get_path_under_work_dir('config', 'world_patrol')

    finished_unique_id = [] if finished is None else [i.unique_id for i in finished]

    for planet in PLANET_LIST:
        planet_dir_path = os.path.join(dir_path, planet.np_id)
        for filename in os.listdir(planet_dir_path):
            idx = filename.find('.yml')
            if idx == -1:
                continue
            route_id: WorldPatrolRouteId = WorldPatrolRouteId(planet, filename[0:idx])
            if route_id.unique_id in finished_unique_id:
                continue

            if whitelist is not None:
                if whitelist.type == 'white' and route_id.unique_id not in whitelist.list:
                    continue
                if whitelist.type == 'black' and route_id.unique_id in whitelist.list:
                    continue

            route_id_arr.append(route_id)
    log.info('最终加载 %d 条线路 过滤已完成 %d 条 使用名单 %s',
             len(route_id_arr), len(finished_unique_id), 'None' if whitelist is None else whitelist.id)

    return route_id_arr


def load_all_whitelist_id() -> List[str]:
    """
    加载所有名单
    :return:
    """
    whitelist_id_arr: List[str] = []
    dir_path = os_utils.get_path_under_work_dir('config', 'world_patrol', 'whitelist')
    for filename in os.listdir(dir_path):
        idx = filename.find('.yml')
        if idx == -1:
            continue
        whitelist_id_arr.append(filename[0:idx])

    return whitelist_id_arr
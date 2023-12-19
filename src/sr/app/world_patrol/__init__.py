import os
from typing import List, Optional

import numpy as np

from basic import os_utils
from basic.i18_utils import gt
from basic.log_utils import log
from sr.app import app_record_now_time_str, app_record_current_dt_str, AppRunRecord, AppDescription, \
    register_app
from sr.config import ConfigHolder
from sr.const import map_const
from sr.const.map_const import Planet, Region, TransportPoint, PLANET_2_REGION, REGION_2_SP, PLANET_LIST

WORLD_PATROL = AppDescription(cn='锄大地', id='world_patrol')
register_app(WORLD_PATROL)


class WorldPatrolRouteId:

    def __init__(self, planet: Planet, raw_id: str):
        """
        :param planet: 星球
        :param raw_id: config\world_patrol\{planet}\{raw_id}.yml
        """
        idx = -1
        idx_cnt = 0
        # 统计字符串中含有多少个'_'字符,
        # idx = {字符数} - 1
        # 不需要分层的路线, idx_cnt = 2, 反之 idx_cnt=3
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

    def _init_after_read_file(self):
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
        super().__init__(file_name, sample=False, sub_dir=['world_patrol', 'whitelist'])

    @property
    def valid(self) -> bool:
        return self.type in ['white', 'black'] and len(self.list) > 0

    @property
    def type(self) -> str:
        return self.get('type', 'black')

    @type.setter
    def type(self, new_value: str):
        self.update('type', new_value)

    @property
    def name(self) -> str:
        return self.get('name', '未命名')

    @name.setter
    def name(self, new_value: str):
        self.update('name', new_value)

    @property
    def list(self) -> List[str]:
        return self.get('list', [])

    @list.setter
    def list(self, new_value: List[str]):
        self.update('list', new_value)


class WorldPatrolRecord(AppRunRecord):

    def __init__(self, ):
        self.current_dt: str = app_record_current_dt_str()
        self.finished: List[str] = []
        self.time_cost: dict[str, List] = {}
        super().__init__(WORLD_PATROL.id)

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

        self.update('run_time', app_record_now_time_str(), False)
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


def load_all_route_id(whitelist: WorldPatrolWhitelist = None, finished: List[str] = None) -> List[WorldPatrolRouteId]:
    """
    加载所有路线
    :param whitelist: 白名单
    :param finished: 已完成的列表
    :return:
    """
    route_id_arr: List[WorldPatrolRouteId] = []
    dir_path = os_utils.get_path_under_work_dir('config', 'world_patrol')

    finished_unique_id = [] if finished is None else finished

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
             len(route_id_arr), len(finished_unique_id), 'None' if whitelist is None else whitelist.name)

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


world_patrol_record: Optional[WorldPatrolRecord] = None


def get_record() -> WorldPatrolRecord:
    global world_patrol_record
    if world_patrol_record is None:
        world_patrol_record = WorldPatrolRecord()
    return world_patrol_record


class WorldPatrolConfig(ConfigHolder):

    def __init__(self):
        super().__init__('world_patrol')

    @property
    def team_num(self) -> int:
        return self.get('team_num', 0)

    @team_num.setter
    def team_num(self, new_value: int):
        self.update('team_num', new_value)

    @property
    def whitelist_id(self) -> str:
        return self.get('whitelist_id', '')

    @whitelist_id.setter
    def whitelist_id(self, new_value: str):
        self.update('whitelist_id', new_value)


world_patrol_config: Optional[WorldPatrolConfig] = None


def get_config() -> WorldPatrolConfig:
    global world_patrol_config
    if world_patrol_config is None:
        world_patrol_config = WorldPatrolConfig()
    return world_patrol_config

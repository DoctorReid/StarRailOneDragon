import os
import threading
from typing import List, Iterator

from basic import os_utils
from basic.i18_utils import gt
from basic.log_utils import log
from sr import constants
from sr.app import Application
from sr.config import ConfigHolder, game_config
from sr.constants.map import TransportPoint, region_with_another_floor, Region, PLANET_LIST, Planet, PLANET_2_REGION, \
    REGION_2_SP
from sr.context import Context, get_context
from sr.image.sceenshot import large_map, LargeMapInfo, mini_map_angle_alas
from sr.operation import Operation
from sr.operation.combine.transport import Transport
from sr.operation.unit.enter_auto_fight import EnterAutoFight
from sr.operation.unit.interact import Interact
from sr.operation.unit.move_directly import MoveDirectly
from sr.operation.unit.wait_in_world import WaitInWorld


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
        return '%s_%s_%s' % (gt(self.planet.cn), gt(self.region.cn), gt(self.tp.cn)) + ('' if self.route_num == 0 else '_%02d' % self.route_num)

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

    def init_from_data(self, author: List[str], planet: str, region: str, tp: str, level: int, route: List):
        self.author_list = author
        self.tp: TransportPoint = constants.map.get_sp_by_cn(planet, region, level, tp)
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
        self.dt: str = None
        self.finished: List = None
        super().__init__('record', sample=False, sub_dir=['world_patrol'])

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


class WorldPatrol(Application):

    def __init__(self, ctx: Context, restart: bool = False, whitelist: WorldPatrolWhitelist = None):
        super().__init__(ctx)
        self.route_list = []
        self.first: bool = True
        self.restart: bool = restart
        self.record: WorldPatrolRecord = None
        self.route_iterator: Iterator = None
        self.whitelist: WorldPatrolWhitelist = whitelist
        self.current_route_idx: int = -1

    def init_app(self):
        self.route_list = load_all_route_id(self.whitelist)
        if self.whitelist is not None:
            log.info('使用白名单 %s' % self.whitelist.id)
        log.info('共加载 %d 条线路', len(self.route_list))
        try:
            self.record = WorldPatrolRecord(os_utils.get_dt(), restart=self.restart)
            log.info('之前已完成线路 %d 条', len(self.record.finished))
        except Exception:
            log.info('读取运行记录失败 重新开始', exc_info=True)

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

    def run(self) -> int:
        self.current_route_idx += 1
        if self.current_route_idx >= len(self.route_list):
            log.info('所有线路执行完毕')
            return Operation.SUCCESS

        route_id = self.route_list[self.current_route_idx]

        if self.run_one_route(route_id):
            self.first = False

        return Operation.WAIT

    def run_one_route(self, route_id: WorldPatrolRouteId) -> bool:
        """
        :param route_id:
        :return: 是否执行成功当前线路
        """
        route: WorldPatrolRoute = WorldPatrolRoute(route_id)
        log.info('准备执行线路 %s %s %s %s', route_id, route.tp.planet.cn, route.tp.region.cn, route.tp.cn)

        if self.record is not None and route_id.unique_id in self.record.finished:
            log.info('线路 %s 之前已执行 跳过', route_id.display_name)
            return False

        log.info('感谢以下人员提供本路线 %s', route.author_list)
        log.info('准备传送 %s %s %s', route.tp.planet.cn, route.tp.region.cn, route.tp.cn)
        op = Transport(self.ctx, route.tp, self.first)
        if not op.execute():
            log.error('传送失败 即将跳过本次路线 %s', route_id.display_name)
            return False
        else:
            log.info('传送完成 开始寻路')

        last_region = route.tp.region
        lm_info = large_map.analyse_large_map(last_region, self.ctx.ih)
        current_pos = route.tp.lm_pos
        for i in range(len(route.route_list)):
            route_item = route.route_list[i]
            next_route_item = route.route_list[i + 1] if i < len(route.route_list) - 1 else None
            if route_item['op'] == 'move':
                result, next_pos, next_lm_info = self.move(route_item['data'], lm_info, current_pos,
                                                           next_route_item is None or next_route_item['op'] != 'move')
                if not result:
                    log.error('寻路失败 即将跳过本次路线 %s', route_id)
                    return False

                current_pos = next_pos
                if next_lm_info is not None:
                    lm_info = next_lm_info
            elif route_item['op'] == 'patrol':
                self.patrol()
            elif route_item['op'] == 'interact':
                result = self.interact(route_item['data'])
                if not result:
                    log.error('交互失败 即将跳过本次路线 %s', route_id)
                    return False
            elif route_item['op'] == 'wait':
                result = self.wait(route_item['data'])
                if not result:
                    log.error('等待失败 即将跳过本次路线 %s', route_id)
                    return False
            elif route_item['op'] == 'update_pos':
                next_pos = route_item['data']
                if len(next_pos) > 2:
                    next_region = constants.map.region_with_another_floor(lm_info.region, next_pos[2])
                    lm_info = large_map.analyse_large_map(next_region, self.ctx.ih)
                current_pos = next_pos[:2]
            else:
                log.error('错误的锄大地指令 %s 即将跳过本次路线 %s', route_item['op'], route_id)
                return False

        self.save_record(route_id)
        return True

    def save_record(self, route_id: WorldPatrolRouteId):
        """
        保存当天运行记录
        :param route_id: 路线ID
        :return:
        """
        self.record.finished.append(route_id.unique_id)
        self.record.save()

    def move(self, p, lm_info: LargeMapInfo, current_pos, stop_afterwards: bool):
        """
        移动到某个点
        :param p: 下一个目标点
        :param lm_info: 小地图信息
        :param current_pos: 当前位置
        :param stop_afterwards: 是否最后停止
        :return:
        """
        target_pos = (p[0], p[1])
        next_lm_info = None
        if len(p) > 2:  # 需要切换层数
            next_region = region_with_another_floor(lm_info.region, p[2])
            next_lm_info = large_map.analyse_large_map(next_region, self.ctx.ih)
        op = MoveDirectly(self.ctx, lm_info, next_lm_info=next_lm_info,
                          target=target_pos, start=current_pos, stop_afterwards=stop_afterwards)

        result = op.execute()

        return result, target_pos, next_lm_info

    def patrol(self) -> bool:
        """
        攻击附近的怪物
        :return:
        """
        op = EnterAutoFight(self.ctx)
        return op.execute()

    def interact(self, cn: str) -> bool:
        """
        交互
        :param cn:
        :return:
        """
        op = Interact(self.ctx, cn, wait=0)
        return op.execute()

    def wait(self, wait_type: str) -> bool:
        """
        等待
        :param wait_type: 等待类型
        :return:
        """
        op: Operation = None
        if wait_type == 'in_world':
            op = WaitInWorld(self.ctx)
        else:
            log.error('错误的wait类型 %s', wait_type)
            return False

        return op.execute()


def load_all_route_id(whitelist: WorldPatrolWhitelist = None) -> List[WorldPatrolRouteId]:
    """
    加载所有路线
    :param whitelist: 白名单
    :return:
    """
    route_id_arr: List[WorldPatrolRouteId] = []
    dir_path = os_utils.get_path_under_work_dir('config', 'world_patrol')
    for planet in PLANET_LIST:
        planet_dir_path = os.path.join(dir_path, planet.np_id)
        for filename in os.listdir(planet_dir_path):
            idx = filename.find('.yml')
            if idx == -1:
                continue
            route_id: WorldPatrolRouteId = WorldPatrolRouteId(planet, filename[0:idx])
            if whitelist is not None:
                if whitelist.type == 'white' and route_id.unique_id not in whitelist.list:
                    continue
                if whitelist.type == 'black' and route_id.unique_id in whitelist.list:
                    continue
            route_id_arr.append(route_id)
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


if __name__ == '__main__':
    ctx = get_context()
    ctx.running = True
    ctx.controller.init()
    app = WorldPatrol(ctx)
    app.execute()

import os
from typing import List

from basic import os_utils
from basic.i18_utils import gt
from basic.log_utils import log
from sr import constants
from sr.app import Application
from sr.config import ConfigHolder
from sr.constants.map import TransportPoint, region_with_another_floor
from sr.context import Context, get_context
from sr.image.sceenshot import large_map, LargeMapInfo
from sr.operation import Operation
from sr.operation.combine.transport import Transport
from sr.operation.unit.enter_auto_fight import EnterAutoFight
from sr.operation.unit.interactive import Interactive
from sr.operation.unit.move_directly import MoveDirectly
from sr.operation.unit.wait_in_world import WaitInWorld


class WorldPatrolRoute(ConfigHolder):

    def __init__(self, route_id: str):
        self.tp: TransportPoint = None
        self.route_list: List = None
        self.route_id: str = route_id
        self.route_name: str = route_id[12:]  # 用于界面展示
        super().__init__(route_id, sample=False, sub_dir='world_patrol')

    def init(self):
        self.init_from_data(**self.data)

    def init_from_data(self, planet: str, region: str, tp: str, level: int, route: List):
        self.tp: TransportPoint = constants.map.get_sp_by_cn(planet, region, level, tp)
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


class WorldPatrol(Application):

    def __init__(self, ctx: Context, restart: bool = False):
        super().__init__(ctx)
        self.route_list = []
        self.first: bool = True
        self.restart: bool = restart
        self.record: WorldPatrolRecord = None
        self.route_iterator = iter(self.route_list)

    def init_app(self):
        self.route_list = load_all_route_id()
        log.info('共加载 %d 条线路', len(self.route_list))
        self.record = WorldPatrolRecord(os_utils.get_dt(), restart=self.restart)
        log.info('之前已完成线路 %d 条', len(self.record.finished))

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
        lm_info = large_map.analyse_large_map(last_region, self.ctx.ih)
        current_pos = route.tp.lm_pos
        for i in range(len(route.route_list)):
            route_item = route.route_list[i]
            next_route_item = route.route_list[i + 1] if i < len(route.route_list) - 1 else None
            if route_item['op'] == 'move':
                result, next_pos, next_lm_info = self.move(route_item['data'], lm_info, current_pos,
                                                           next_route_item is not None and next_route_item['op'] != 'move')
                if not result:
                    log.error('寻路失败 即将跳过本次路线 %s', route_id)
                    return

                current_pos = next_pos
                if next_lm_info is not None:
                    lm_info = next_lm_info
            elif route_item['op'] == 'patrol':
                self.patrol()
            elif route_item['op'] == 'interactive':
                result = self.interactive(route_item['data'])
                if not result:
                    log.error('交互失败 即将跳过本次路线 %s', route_id)
                    return
            elif route_item['op'] == 'wait':
                result = self.wait(route_item['data'])
                if not result:
                    log.error('等待失败 即将跳过本次路线 %s', route_id)
                    return
            else:
                log.error('错误的锄大地指令 %s 即将跳过本次路线 %s', route_item['op'], route_id)
                return

        self.save_record(route_id)

    def save_record(self, route_id):
        """
        保存当天运行记录
        :param route_id: 路线ID
        :return:
        """
        self.record.finished.append(route_id)
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

    def interactive(self, cn: str) -> bool:
        """
        交互
        :param cn:
        :return:
        """
        op = Interactive(self.ctx, cn, wait=2)
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


def load_all_route_id() -> List[str]:
    """
    加载所有路线
    :return:
    """
    route_id_arr: List[str] = []
    dir_path = os_utils.get_path_under_work_dir('config', 'world_patrol')
    for filename in os.listdir(dir_path):
        if filename == 'record.yml':
            continue
        idx = filename.find('.yml')
        if idx == -1:
            continue
        route_id_arr.append(filename[0:idx])
    return route_id_arr


if __name__ == '__main__':
    ctx = get_context()
    ctx.running = True
    ctx.controller.init()
    app = WorldPatrol(ctx)
    app.execute()

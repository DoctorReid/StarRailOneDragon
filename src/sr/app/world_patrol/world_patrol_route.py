import os
from typing import Optional, List, Tuple, Any

import yaml

from basic import os_utils, Point
from basic.i18_utils import gt
from basic.log_utils import log
from sr.app.world_patrol.world_patrol_whitelist_config import WorldPatrolWhitelist
from sr.const import map_const, operation_const
from sr.const.map_const import Planet, Region, TransportPoint, PLANET_2_REGION, REGION_2_SP, PLANET_LIST


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
        self.region: Optional[Region] = None
        self.tp: Optional[TransportPoint] = None

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

        self.raw_id = raw_id

    @property
    def display_name(self):
        """
        用于前端显示路线名称
        :return:
        """
        return '%s_%s_%s' % (gt(self.planet.cn, 'ui'), gt(self.region.cn, 'ui'), gt(self.tp.cn, 'ui')) + ('' if self.route_num == 0 else '_%02d' % self.route_num)

    @property
    def unique_id(self) -> str:
        """
        唯一标识 用于各种配置中保存
        :return:
        """
        return '%s_%s_%s' % (self.planet.np_id, self.region.r_id, self.tp.id) + ('' if self.route_num == 0 else '_%02d' % self.route_num)

    def equals(self, another_route_id):
        return another_route_id is not None and self.planet == another_route_id.planet and self.raw_id == another_route_id.raw_id

    @property
    def yml_file_path(self) -> str:
        """
        配置文件的目录
        :return:
        """
        dir_path = get_route_dir(self.planet)
        return os.path.join(dir_path, '%s.yml' % self.raw_id)


def get_route_dir(planet: Planet) -> str:
    """
    返回星球路线文件夹
    :param planet:
    :return:
    """
    return os_utils.get_path_under_work_dir('config', 'world_patrol', planet.np_id)


def new_route_id(planet: Planet, region: Region, tp: TransportPoint) -> WorldPatrolRouteId:
    """
    返回一个新的路线ID
    :param planet: 星球
    :param region: 区域
    :param tp: 传送点
    :return:
    """
    same_region_cnt: int = 0
    same_tp_cnt: int = 0
    dir_path = get_route_dir(planet)
    for filename in os.listdir(dir_path):
        idx = filename.find('.yml')
        if idx == -1:
            continue
        if not filename.startswith(region.r_id):
            continue
        same_region_cnt += 1
        tp_suffix = filename[len(region.r_id) + 5:idx]
        if not tp_suffix.startswith(tp.id):
            continue
        same_tp_cnt += 1

    raw_id = '%s_R%02d_%s' % (region.r_id, same_region_cnt + 1, tp.id) + (
        '' if same_tp_cnt == 0 else '_%d' % (same_tp_cnt + 1))
    return WorldPatrolRouteId(planet, raw_id)


class WorldPatrolRouteOperation:

    def __init__(self, op: str, data: Any = None, idx: int = 0):
        self.op: str = op
        """指令类型 operation_const"""

        self.data: Any = data
        """
        指令数据
        move, update_pos: (x, y, floor) - 坐标和切换楼层
        patrol, disposable: 攻击，无data
        interact: 交互文本
        wait: (type, timeout) - 等待类型和超时时间
        """

        self.idx: int = idx
        """指令下标 仅在画图时有用"""


class WorldPatrolRoute:

    def __init__(self, route_id: WorldPatrolRouteId):
        self.author_list: List[str] = []
        self.tp: Optional[TransportPoint] = None
        self.route_list: List[WorldPatrolRouteOperation] = []

        self.route_id: WorldPatrolRouteId = route_id
        self.is_new: bool = False  # 新否新路线未保存
        self.read_from_file()

    @property
    def yml_file_path(self) -> str:
        """
        配置文件的目录
        :return:
        """
        dir_path = get_route_dir(self.route_id.planet)
        return os.path.join(dir_path, '%s.yml' % self.route_id.raw_id)

    def read_from_file(self):
        file_path = self.yml_file_path
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                yaml_data = yaml.safe_load(file)
                self.init_from_yaml_data(yaml_data)
        else:
            self.author_list = []
            self.tp = self.route_id.tp
            self.route_list = []
            self.is_new = True

    def init_from_yaml_data(self, yaml_data: dict):
        self.author_list = yaml_data.get('author', [])
        self.tp = self.route_id.tp
        yml_route_list = yaml_data.get('route', [])
        self.route_list = []
        for yml_route_item in yml_route_list:
            item = WorldPatrolRouteOperation(op=yml_route_item['op'],
                                             data=yml_route_item.get('data', None))
            self.route_list.append(item)
        self.init_idx()

    def init_idx(self):
        """
        重新初始化下标
        :return:
        """
        idx = 1
        for item in self.route_list:
            item.idx = idx
            idx += 1

    @property
    def display_name(self):
        return self.route_id.display_name

    def save(self):
        """
        保存
        :return:
        """
        file_path = self.yml_file_path
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(self.route_config_str)
        log.info('保存成功 %s', file_path)
        self.is_new = False

    def delete(self):
        """
        删除路线
        :return:
        """
        file_path = self.yml_file_path
        if os.path.exists(file_path):
            os.remove(file_path)
        log.info('删除成功 %s', file_path)

    def add_author(self, new_author: str, save: bool = True):
        """
        增加一个作者
        :param new_author: 作者名称
        :param save: 是否保存
        :return:
        """
        if self.author_list is None:
            self.author_list = []
        if new_author not in self.author_list:
            self.author_list.append(new_author)
        if save:
            self.save()

    @property
    def route_config_str(self) -> str:
        cfg: str = ''
        if self.tp is None:
            return cfg
        last_floor = self.tp.region.floor
        cfg += "author: %s\n" % self.author_list
        cfg += "planet: '%s'\n" % self.tp.planet.cn
        cfg += "region: '%s'\n" % self.tp.region.cn
        cfg += "floor: %d\n" % last_floor
        cfg += "tp: '%s'\n" % self.tp.cn
        cfg += "route:\n"
        for route_item in self.route_list:
            cfg += f"  - idx: {route_item.idx}\n"
            if route_item.op in [operation_const.OP_MOVE, operation_const.OP_SLOW_MOVE,
                                    operation_const.OP_UPDATE_POS]:
                cfg += "    op: '%s'\n" % route_item.op
                pos = route_item.data
                if len(pos) > 2 and pos[2] != last_floor:
                    cfg += "    data: [%d, %d, %d]\n" % (pos[0], pos[1], pos[2])
                    last_floor = pos[2]
                else:
                    cfg += "    data: [%d, %d]\n" % (pos[0], pos[1])
            elif route_item.op in [operation_const.OP_PATROL, operation_const.OP_DISPOSABLE, operation_const.OP_CATAPULT]:
                cfg += "    op: '%s'\n" % route_item.op
            elif route_item.op == operation_const.OP_INTERACT:
                cfg += "    op: '%s'\n" % route_item.op
                cfg += "    data: '%s'\n" % route_item.data
            elif route_item.op == operation_const.OP_WAIT:
                cfg += "    op: '%s'\n" % route_item.op
                cfg += "    data: ['%s', '%s']\n" % (route_item.data[0], route_item.data[1])
            elif route_item.op == operation_const.OP_ENTER_SUB:
                cfg += "    op: '%s'\n" % route_item.op
                cfg += "    data: ['%s', '%s']\n" % (route_item.data[0], route_item.data[1])

        return cfg

    @property
    def last_pos(self) -> Tuple[Region, Point]:
        """
        返回最后一个点的坐标
        :return:
        """
        region = self.tp.region
        pos = self.tp.tp_pos
        if self.route_list is None or len(self.route_list) == 0:
            return region, pos
        for op in self.route_list:
            if op.op in [operation_const.OP_MOVE, operation_const.OP_SLOW_MOVE, operation_const.OP_UPDATE_POS]:
                pos = Point(op.data[0], op.data[1])
                if len(op.data) > 2:
                    region = map_const.region_with_another_floor(region, op.data[2])
            elif op.op == operation_const.OP_ENTER_SUB:
                region = map_const.get_sub_region_by_cn(op.data[0], region, int(op.data[1]))
                pos = None

        return region, pos

    def add_move(self, x: int, y: int, floor: int):
        """
        在最后添加一个移动的指令
        :param x: 横坐标
        :param y: 纵坐标
        :param floor: 楼层
        :return:
        """
        last_region, last_pos = self.last_pos

        if last_region.floor == floor:
            to_add = WorldPatrolRouteOperation(op=operation_const.OP_MOVE, data=(x, y))
        else:
            to_add = WorldPatrolRouteOperation(op=operation_const.OP_MOVE, data=(x, y, floor))

        self.route_list.append(to_add)
        self.init_idx()

    def pop_last(self):
        """
        取消最后一个指令
        :return:
        """
        if len(self.route_list) > 0:
            self.route_list.pop()

    def reset(self, new_route_list: Optional[List] = None):
        """
        重置所有指令
        :return:
        """
        if new_route_list is None:
            self.route_list = []
        else:
            self.route_list = new_route_list

    def add_patrol(self):
        """
        增加攻击指令
        :return:
        """
        to_add = WorldPatrolRouteOperation(op=operation_const.OP_PATROL)
        self.route_list.append(to_add)
        self.init_idx()

    def add_disposable(self):
        """
        增加攻击可破坏物指令
        :return:
        """
        to_add = WorldPatrolRouteOperation(op=operation_const.OP_DISPOSABLE)
        self.route_list.append(to_add)
        self.init_idx()

    def add_interact(self, interact_text: str):
        """
        增加交互指令
        :param interact_text: 交互文本
        :return:
        """
        to_add = WorldPatrolRouteOperation(op=operation_const.OP_INTERACT, data=interact_text)
        self.route_list.append(to_add)
        self.init_idx()

    def add_catapult(self):
        """
        增加交互指令
        :param interact_text: 交互文本
        :return:
        """
        to_add = WorldPatrolRouteOperation(op=operation_const.OP_CATAPULT)
        self.route_list.append(to_add)
        self.init_idx()

    def add_wait(self, wait_type: str, wait_timeout: int):
        """
        增加等待指令
        :return:
        """
        to_add = WorldPatrolRouteOperation(op=operation_const.OP_WAIT, data=[wait_type, wait_timeout])
        self.route_list.append(to_add)
        self.init_idx()

    def mark_last_as_update(self):
        """
        将最后一个指令变更为更新位置
        :return:
        """
        idx = len(self.route_list) - 1
        if self.route_list[idx].op in [operation_const.OP_MOVE, operation_const.OP_SLOW_MOVE]:
            self.route_list[idx].op = operation_const.OP_UPDATE_POS

    def switch_slow_move(self):
        """
        将最后一个移动标记成慢走 或从慢走标记成可疾跑
        :return:
        """
        if self.empty_op:
            return

        last_op = self.route_list[len(self.route_list) - 1]
        if last_op.op not in [operation_const.OP_MOVE, operation_const.OP_SLOW_MOVE]:
            return

        if last_op.op == operation_const.OP_MOVE:
            last_op.op = operation_const.OP_SLOW_MOVE
        else:
            last_op.op = operation_const.OP_MOVE

    def switch_floor(self, new_floor: int):
        """
        在最后一个移动指令中变更楼层
        :param new_floor:
        :return:
        """
        if self.empty_op:
            return

        last_idx = len(self.route_list) - 1
        last_op = self.route_list[last_idx]
        if last_op.op not in [operation_const.OP_MOVE, operation_const.OP_SLOW_MOVE]:
            return

        self.route_list[last_idx].data = (
            self.route_list[last_idx].data[0],
            self.route_list[last_idx].data[1],
            new_floor
        )

    def enter_sub_region(self, sub_region_cn: str, floor: int):
        self.route_list.append(WorldPatrolRouteOperation(op=operation_const.OP_ENTER_SUB, data=[sub_region_cn, str(floor)]))

    @property
    def empty_op(self) -> bool:
        """
        当前指令为空
        :return:
        """
        return self.route_list is None or len(self.route_list) == 0

    @property
    def last_sub_region_op(self) -> Optional[WorldPatrolRouteOperation]:
        """
        最后一个子区域的中文
        :return:
        """
        if self.empty_op:
            return None
        op = None
        for o in self.route_list:
            if o.op == operation_const.OP_ENTER_SUB:
                op = o
        return op


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
        if not os.path.exists(planet_dir_path):
            continue
        for filename in os.listdir(planet_dir_path):
            idx = filename.find('.yml')
            if idx == -1:
                continue
            route_id: WorldPatrolRouteId = WorldPatrolRouteId(planet, filename[0:idx])
            if route_id.tp is None:
                log.error('存在无效路线 %s', route_id.yml_file_path)
                continue
            if route_id.unique_id in finished_unique_id:
                continue

            if whitelist is not None:
                if whitelist.type == 'white' and route_id.unique_id not in whitelist.list:
                    continue
                if whitelist.type == 'black' and route_id.unique_id in whitelist.list:
                    continue

            route_id_arr.append(route_id)

    # 按白名单的顺序排列
    if whitelist is not None and whitelist.type == 'white':
        uid_2_route: dict[str, WorldPatrolRouteId] = {}
        for route_id in route_id_arr:
            uid_2_route[route_id.unique_id] = route_id
        route_id_arr = []

        for uid in whitelist.list:
            if uid in uid_2_route:
                route_id_arr.append(uid_2_route[uid])

    log.info('最终加载 %d 条线路 过滤已完成 %d 条 使用名单 %s',
             len(route_id_arr), len(finished_unique_id), 'None' if whitelist is None else whitelist.name)

    return route_id_arr

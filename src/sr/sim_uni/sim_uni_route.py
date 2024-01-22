import os
import shutil
from typing import TypedDict, Union, List, Optional

import cv2
import yaml
from cv2.typing import MatLike

from basic import Point, os_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.const import operation_const
from sr.const.map_const import Region, get_planet_by_cn, get_region_by_cn
from sr.sim_uni.sim_uni_const import UNI_NUM_CN, SimUniLevelType


class SimUniRouteOperation(TypedDict):

    op: str
    data: Union[List[int], str]


class SimUniRoute:

    def __init__(self, uni_num: int, level_type: SimUniLevelType,
                 idx: Optional[int] = None
                 ):
        """
        模拟宇宙路线配置，每条路线最后应该结束在选择下一关之前
        :param uni_num: 第几宇宙
        :param level_type: 楼层类型
        :param idx: 下标。为空时说明是新建路线
        """
        self.uni_num: int = uni_num
        self.level_type: SimUniLevelType = level_type

        self.idx: Optional[int] = None
        self.mm: Optional[MatLike] = None
        self.mm2: Optional[MatLike] = None  # 有极少数地图 重进后初始小地图不一样
        self.region: Optional[Region] = None
        self.start_pos: Optional[Point] = None
        self.op_list: Optional[List[SimUniRouteOperation]] = None

        if idx is None:
            self._create_new_route()
        else:
            self.idx = idx
            self._read_route()

    def load_from_route_yml(self, data):
        planet = get_planet_by_cn(data['planet'])
        self.region = get_region_by_cn(data['region'], planet, data['floor'])
        self.start_pos = Point(data['start_pos'][0], data['start_pos'][1])
        self.op_list = data['op_list']

    def _create_new_route(self):
        """
        新建一个模拟宇宙路线
        :return:
        """
        base_dir = SimUniRoute.get_uni_base_dir(self.uni_num, self.level_type.route_id)
        self.idx = 1  # 获取合法的下标
        while True:
            route_dir = os.path.join(base_dir, '%03d' % self.idx)
            if os.path.exists(route_dir):
                self.idx += 1
            else:
                break
        self.op_list = []

    def _read_route(self):
        dir_path = self.get_route_dir_path()
        self.mm = cv2_utils.read_image(os.path.join(dir_path, 'mm.png'))
        self.mm2 = cv2_utils.read_image(os.path.join(dir_path, 'mm2.png'))
        with open(os.path.join(dir_path, 'route.yml'), 'r', encoding='utf-8') as file:
            route = yaml.safe_load(file)
            self.load_from_route_yml(route)

    @property
    def uid(self) -> str:
        """
        路线唯一标识 = 第几宇宙 + 楼层类型 + 下标
        :return:
        """
        return SimUniRoute.get_uid(self.uni_num, self.level_type.route_id, self.idx)

    @property
    def display_name(self) -> str:
        """
        展示名称
        :return:
        """
        return '%s %s %03d %s' % (
            gt('第%s宇宙' % UNI_NUM_CN[self.uni_num], 'ui'),
            gt(self.level_type.type_name, 'ui'),
            self.idx,
            self.region.display_name
        )

    @staticmethod
    def get_uni_base_dir(uni_num: int, level_type: str) -> str:
        """
        获取选定宇宙对应的文件夹位置
        :param uni_num:
        :param level_type:
        :return:
        """
        return os_utils.get_path_under_work_dir('config', 'sim_uni',
                                                '%02d' % uni_num,
                                                '%s' % level_type)

    @staticmethod
    def get_uid(uni_num: int, level_type: str, idx: int) -> str:
        """
        路线唯一标识 = 第几宇宙 + 楼层类型 + 下标
        :return:
        """
        return '%02d_%s_%03d' % (uni_num, level_type, idx)

    def get_route_dir_path(self) -> str:
        """
        获取路线对应文件夹的位置
        :return:
        """
        return os_utils.get_path_under_work_dir('config', 'sim_uni',
                                                '%02d' % self.uni_num,
                                                '%s' % self.level_type.route_id,
                                                '%03d' % self.idx)

    def save(self):
        """
        保存
        :return:
        """
        route_dir = self.get_route_dir_path()
        mm_path = os.path.join(route_dir, 'mm.png')
        if not os.path.exists(mm_path):
            cv2.imwrite(mm_path, self.mm)

        route_path = os.path.join(route_dir, 'route.yml')
        with open(route_path, "w", encoding="utf-8") as file:
            file.write(self.get_route_text())

    def get_route_text(self) -> str:
        """
        获取当前路线的文本
        :return:
        """
        cfg: str = ''
        if self.region is None:
            return cfg

        cfg += "planet: '%s'\n" % self.region.planet.cn
        cfg += "region: '%s'\n" % self.region.cn
        cfg += "floor: %d\n" % self.region.floor
        cfg += "start_pos: [%d, %d]\n" % (self.start_pos.x, self.start_pos.y)
        if len(self.op_list) == 0:
            cfg += "op_list: []\n"
        else:
            cfg += "op_list:\n"
            last_floor = self.region.floor
            for route_item in self.op_list:
                if route_item['op'] in [operation_const.OP_MOVE, operation_const.OP_SLOW_MOVE, operation_const.OP_UPDATE_POS]:
                    cfg += "  - op: '%s'\n" % route_item['op']
                    pos = route_item['data']
                    if len(pos) > 2 and pos[2] != last_floor:
                        cfg += "    data: [%d, %d, %d]\n" % (pos[0], pos[1], pos[2])
                        last_floor = pos[2]
                    else:
                        cfg += "    data: [%d, %d]\n" % (pos[0], pos[1])
                elif route_item['op'] == operation_const.OP_PATROL:
                    cfg += "  - op: '%s'\n" % route_item['op']
                elif route_item['op'] == operation_const.OP_INTERACT:
                    cfg += "  - op: '%s'\n" % route_item['op']
                    cfg += "    data: '%s'\n" % route_item['data']
                elif route_item['op'] == operation_const.OP_WAIT:
                    cfg += "  - op: '%s'\n" % route_item['op']
                    cfg += "    data: ['%s', '%s']\n" % (route_item['data'][0], route_item['data'][1])
        return cfg

    def delete(self):
        """
        删除路线
        :return:
        """
        route_dir = self.get_route_dir_path()
        shutil.rmtree(route_dir)

import os
from typing import List, Optional

from one_dragon.base.config.yaml_operator import YamlOperator
from one_dragon.base.geometry.point import Point
from one_dragon.utils import os_utils, str_utils
from one_dragon.utils.i18_utils import gt


class Planet:

    def __init__(self, num: int, uid: str, cn: str):
        self.num: int = num  # 编号 用于强迫症给文件排序
        self.id: str = uid  # 用在找文件夹之类的
        self.cn: str = cn  # 中文

    def __repr__(self):
        return '%02d - %s' % (self.num, self.cn)

    @property
    def n_id(self):
        """
        编号ID
        :return:
        """
        return 'P%02d' % self.num

    @property
    def np_id(self):
        """
        带编号的唯一ID
        :return:
        """
        return '%s_%s' % (self.n_id, self.id)

    @property
    def display_name(self):
        return gt(self.cn, 'ui')


class Region:

    def __init__(self, num: int, uid: str, cn: str, planet: Planet,
                 floor: int = 0,
                 parent: Optional = None,
                 enter_template_id: Optional[str] = None,
                 enter_lm_pos: Optional[Point] = None,
                 large_map_scale: Optional[int] = None):
        self.num: int = num  # 编号 方便列表排序
        self.id: str = uid  # id 用在找文件夹之类的
        self.cn: str = cn  # 中文 用在OCR
        self.planet: Planet = planet
        self.floor: int = floor
        self.parent: Region = parent  # 子区域才会有 属于哪个具体区域
        self.enter_template_id: str = enter_template_id  # 子区域才会有 入口对应的模板ID
        self.enter_lm_pos: Point = enter_lm_pos  # 子区域才会有 在具体区域的哪个位置进入
        self.large_map_scale: int = 0 if large_map_scale is None else large_map_scale

    def __repr__(self):
        return '%s - %s' % (self.cn, self.id)

    @property
    def r_id(self) -> str:
        """
        星球+区域ID 用于不区分楼层的场景
        :return:
        """
        return 'R%02d_%s' % (self.num, self.id)

    @property
    def pr_id(self) -> str:
        """
        星球+区域ID 用于不区分楼层的场景
        :return:
        """
        return '%s_%s' % (self.planet.np_id, self.r_id)

    @property
    def l_str(self) -> str:
        """
        层数 正数用 l1 负数用 b1
        :return:
        """
        if self.floor == 0:
            return ''
        elif self.floor > 0:
            return '_F%d' % self.floor
        elif self.floor < 0:
            return '_B%d' % abs(self.floor)

    @property
    def rl_id(self) -> str:
        """
        区域在星球下的唯一ID 用于文件夹
        :return 区域id + 楼层id
        """
        return '%s%s' % (self.r_id, self.l_str)

    @property
    def prl_id(self) -> str:
        """
        区域唯一ID 用于唯一标识
        :return 星球id + 区域id + 楼层id
        """
        return '%s_%s' % (self.planet.np_id, self.rl_id)

    @property
    def another_floor(self) -> bool:
        return self.floor != 0

    @property
    def display_name(self) -> str:
        if self.another_floor:
            return '%s %s' % (gt(self.cn, 'ui'), gt('%d层' % self.floor, 'ocr'))
        else:
            return gt(self.cn, 'ui')


class SpecialPoint:

    def __init__(self, uid: str, cn: str, region: Region, template_id: str, lm_pos: tuple, tp_pos: Optional[tuple] = None):
        self.id: str = uid  # 英文 用在找图
        self.cn: str = cn  # 中文 用在OCR
        self.region: Region = region  # 所属区域
        self.planet: Planet = region.planet  # 所属星球
        self.template_id: str = template_id  # 匹配模板
        self.lm_pos: Point = Point(lm_pos[0], lm_pos[1])  # 在大地图的坐标
        self.tp_pos: Point = Point(tp_pos[0], tp_pos[1]) if tp_pos is not None else self.lm_pos  # 传送落地的坐标

    def __repr__(self):
        return '%s - %s' % (self.cn, self.id)

    @property
    def display_name(self):
        return gt(self.cn, 'ui')

    @property
    def unique_id(self):
        return '%s_%s' % (self.region.prl_id, self.id)


class WorldPatrolMapData:

    def __init__(self):
        self.planet_list: List[Planet] = []
        self.region_list: List[Region] = []
        self.sp_list: List[SpecialPoint] = []
        self.region_2_sp: dict[str, List[SpecialPoint]] = {}

        self.load_map_data()

    def load_map_data(self) -> None:
        """
        加载数据
        :return:
        """
        self.load_planet_data()
        self.load_region_data()
        self.load_special_point_data()

    @staticmethod
    def get_map_data_dir() -> str:
        return os_utils.get_path_under_work_dir('assets', 'game_data', 'world_patrol_map')

    def load_planet_data(self) -> None:
        """
        加载星球数据
        :return:
        """
        file_path = os.path.join(self.get_map_data_dir(), 'planet.yml')
        yaml_op = YamlOperator(file_path)
        self.planet_list = [Planet(**item) for item in yaml_op.data]

    def load_region_data(self) -> None:
        """
        加载区域数据
        :return:
        """
        self.region_list = []

        for p in self.planet_list:
            file_path = os.path.join(self.get_map_data_dir(), p.np_id, f'{p.np_id}.yml')
            yaml_op = YamlOperator(file_path)
            for r in yaml_op.data:
                parent_region_name = r.get('parent_region_name', None)
                parent_region_floor = r.get('parent_region_floor', 0)
                enter_template_id = r.get('enter_template_id', None)
                enter_lm_pos = r.get('enter_lm_pos', [0, 0])

                if parent_region_name is not None:
                    parent_region = self.best_match_region_by_name(parent_region_name, p, parent_region_floor)
                    enter_lm_pos = Point(enter_lm_pos[0], enter_lm_pos[1])
                else:
                    parent_region = None
                    enter_lm_pos = None

                floor_list = r.get('floors', [0])
                for floor in floor_list:
                    region = Region(r['num'], r['uid'], r['cn'], p, floor,
                                    parent=parent_region,
                                    enter_template_id=enter_template_id, enter_lm_pos=enter_lm_pos)

                    self.region_list.append(region)

    def load_special_point_data(self) -> None:
        """
        加载特殊点数据
        :return:
        """
        self.sp_list = []
        self.region_2_sp = {}

        loaded_region_set = set()
        for region in self.region_list:
            if region.pr_id in loaded_region_set:
                continue
            loaded_region_set.add(region.pr_id)

            file_path = os.path.join(self.get_map_data_dir(), region.planet.np_id, f'{region.pr_id}.yml')
            yaml_op = YamlOperator(file_path)

            for sp_data in yaml_op.data:
                real_planet = self.best_match_planet_by_name(sp_data['planet_name'])
                real_region = self.best_match_region_by_name(sp_data['region_name'], real_planet, sp_data.get('region_floor', 0))

                sp = SpecialPoint(sp_data['uid'], sp_data['cn'], real_region, sp_data['template_id'], sp_data['lm_pos'],
                                  sp_data.get('tp_pos', None))
                self.sp_list.append(sp)

                if real_region.pr_id not in self.region_2_sp:
                    self.region_2_sp[real_region.pr_id] = []

                self.region_2_sp[real_region.pr_id].append(sp)

    def get_planet_by_cn(self, cn: str) -> Optional[Planet]:
        """
        根据星球的中文 获取对应常量
        :param cn: 星球中文
        :return: 常量
        """
        for i in self.planet_list:
            if i.cn == cn:
                return i
        return None

    def best_match_planet_by_name(self, ocr_word: str) -> Optional[Planet]:
        """
        根据OCR结果匹配一个星球
        :param ocr_word: OCR结果
        :return:
        """
        planet_names = [gt(p.cn, 'ocr') for p in self.planet_list]
        idx = str_utils.find_best_match_by_difflib(ocr_word, target_word_list=planet_names)
        if idx is None:
            return None
        else:
            return self.planet_list[idx]

    def best_match_region_by_name(self, ocr_word: Optional[str], planet: Optional[Planet] = None,
                                  target_floor: Optional[int] = None) -> Optional[Region]:
        """
        根据OCR结果匹配一个区域 随机返回楼层
        :param ocr_word: OCR结果
        :param planet: 所属星球
        :param target_floor: 目标楼层 不传入时随机一个
        :return:
        """
        if ocr_word is None or len(ocr_word) == 0:
            return None

        to_check_region_list: List[Region] = []
        to_check_region_name_list: List[str] = []

        for region in self.region_list:
            if planet is not None and planet.np_id != region.planet.np_id:
                continue

            if target_floor is not None and target_floor != region.floor:
                continue

            to_check_region_list.append(region)
            to_check_region_name_list.append(gt(region.cn, 'ocr'))

        idx = str_utils.find_best_match_by_difflib(ocr_word, to_check_region_name_list)
        if idx is None:
            return None
        else:
            return to_check_region_list[idx]

    def best_match_sp_by_name(self, region: Region, ocr_word: str) -> Optional[SpecialPoint]:
        """
        在指定区域中 忽略楼层 根据名字匹配对应的特殊点
        :param region: 区域
        :param ocr_word: 特殊点名称
        :return:
        """
        if ocr_word is None or len(ocr_word) == 0:
            return None

        to_check_sp_list: List[SpecialPoint] = self.region_2_sp.get(region.pr_id, [])
        to_check_sp_name_list: List[str] = [gt(i.cn, 'ocr') for i in to_check_sp_list]

        idx = str_utils.find_best_match_by_difflib(ocr_word, to_check_sp_name_list)
        if idx is None:
            return None
        else:
            return to_check_sp_list[idx]



if __name__ == '__main__':
    _data = WorldPatrolMapData()
    print(len(_data.planet_list))
    print(len(_data.region_list))
    print(len(_data.sp_list))

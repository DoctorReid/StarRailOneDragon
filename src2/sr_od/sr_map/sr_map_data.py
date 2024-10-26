import cv2
import os
from cv2.typing import MatLike
from typing import List, Optional

from one_dragon.base.config.yaml_operator import YamlOperator
from one_dragon.base.geometry.point import Point
from one_dragon.base.geometry.rectangle import Rect
from one_dragon.utils import os_utils, str_utils, cv2_utils, cal_utils
from one_dragon.utils.i18_utils import gt
from sr_od.sr_map.large_map_info import LargeMapInfo
from sr_od.sr_map.sr_map_def import Planet, Region, SpecialPoint


class SrMapData:

    def __init__(self):
        self.planet_list: List[Planet] = []
        self.region_list: List[Region] = []
        self.planet_2_region: dict[str, List[Region]] = {}

        self.sp_list: List[SpecialPoint] = []
        self.region_2_sp: dict[str, List[SpecialPoint]] = {}

        self.load_map_data()

        self.large_map_info_map: dict[str, LargeMapInfo] = {}

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
        self.planet_2_region: dict[str, List[Region]] = {}

        for p in self.planet_list:
            file_path = os.path.join(self.get_map_data_dir(), p.np_id, f'{p.np_id}.yml')
            yaml_op = YamlOperator(file_path)
            self.planet_2_region[p.np_id] = []

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
                    self.planet_2_region[p.np_id].append(region)

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

    def get_sub_region_by_cn(self, region: Region, cn: str, floor: int = 0) -> Optional[Region]:
        """
        根据子区域的中文 获取对应常量
        :param region: 所属区域
        :param cn: 子区域名称
        :param floor: 子区域的层数
        :return: 常量
        """
        same_planet_region_list = self.planet_2_region.get(region.planet.np_id, [])
        for r in same_planet_region_list:
            if r.parent is not None and r.parent == region and r.cn == cn and r.floor == floor:
                return r
        return None

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

    def best_match_sp_by_all_name(self, planet_name: str, region_name: str, sp_name: str, region_floor: int = 0) -> Optional[
        SpecialPoint]:
        """
        根据名称 匹配具体的特殊点
        :param planet_name: 星球名称
        :param region_name: 区域名称
        :param sp_name: 特殊点名称
        :param region_floor: 区域楼层
        :return:
        """
        planet = self.best_match_planet_by_name(planet_name)
        region = self.best_match_region_by_name(region_name, planet, region_floor)
        return self.best_match_sp_by_name(region, sp_name)

    def get_sp_type_in_rect(self, region: Region, rect: Rect) -> dict:
        """
        获取区域特定矩形内的特殊点 按种类分组
        :param region: 区域
        :param rect: 矩形 为空时返回全部
        :return: 特殊点
        """
        sp_list = self.region_2_sp.get(region.pr_id)
        sp_map = {}
        if sp_list is None or len(sp_list) == 0:
            return sp_map
        for sp in sp_list:
            if rect is None or cal_utils.in_rect(sp.lm_pos, rect):
                if sp.template_id not in sp_map:
                    sp_map[sp.template_id] = []
                sp_map[sp.template_id].append(sp)

        return sp_map

    def get_region_list_by_planet(self, planet: Planet) -> List[Region]:
        """
        获取星球下的所有区域
        :param planet: 星球
        :return:
        """
        return self.planet_2_region.get(planet.np_id, [])

    def load_large_map_info(self, region: Region) -> LargeMapInfo:
        """
        加载某张大地图到内存中
        :param region: 对应区域
        :return: 地图图片
        """
        dir_path = SrMapData.get_large_map_dir_path(region)
        info = LargeMapInfo()
        info.region = region
        info.raw = cv2_utils.read_image(os.path.join(dir_path, 'raw.png'))
        info.mask = cv2_utils.read_image(os.path.join(dir_path, 'mask.png'))
        self.large_map_info_map[region.prl_id] = info
        return info

    def get_large_map_info(self, region: Region) -> LargeMapInfo:
        """
        获取某张大地图
        :param region: 区域
        :return: 地图图片
        """
        if region.prl_id not in self.large_map_info_map:
            # 尝试加载一次
            return self.load_large_map_info(region)
        else:
            return self.large_map_info_map[region.prl_id]

    @staticmethod
    def get_large_map_dir_path(region: Region):
        """
        获取某个区域的地图文件夹路径
        :param region:
        :return:
        """
        return os.path.join(os_utils.get_path_under_work_dir('assets', 'template', 'large_map',
                                                             region.planet.np_id, region.rl_id))

    @staticmethod
    def get_map_path(region: Region, mt: str = 'raw') -> str:
        """
        获取某张地图路径
        :param region: 对应区域
        :param mt: 地图类型
        :return: 图片路径
        """
        return os.path.join(SrMapData.get_large_map_dir_path(region), '%s.png' % mt)

    @staticmethod
    def save_large_map_image(image: MatLike, region: Region, mt: str = 'raw'):
        """
        保存某张地图
        :param image: 图片
        :param region: 区域
        :param mt: 地图类型
        :return:
        """
        path = SrMapData.get_map_path(region, mt)
        cv2_utils.save_image(image, path)

    @staticmethod
    def get_large_map_image(region: Region, mt: str = 'raw') -> MatLike:
        """
        保存某张地图
        :param region: 区域
        :param mt: 地图类型
        :return:
        """
        path = SrMapData.get_map_path(region, mt)
        return cv2_utils.read_image(path)


if __name__ == '__main__':
    _data = SrMapData()
    print(len(_data.planet_list))
    print(len(_data.region_list))
    print(len(_data.sp_list))

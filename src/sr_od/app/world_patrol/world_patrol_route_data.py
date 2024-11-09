import os
from typing import List, Optional

from one_dragon.base.config.yaml_operator import YamlOperator
from one_dragon.utils import os_utils
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log
from sr_od.sr_map.sr_map_data import SrMapData
from sr_od.sr_map.sr_map_def import Planet, Region, SpecialPoint
from sr_od.app.world_patrol.world_patrol_route import WorldPatrolRoute
from sr_od.app.world_patrol.world_patrol_whitelist_config import WorldPatrolWhitelist


class WorldPatrolRouteData:

    def __init__(self, map_data: SrMapData):
        self.map_data: SrMapData = map_data

    def load_all_route(self, whitelist: WorldPatrolWhitelist = None, finished: List[str] = None,
                       target_planet: Optional[Planet] = None,
                       target_region: Optional[Region] = None) -> List[WorldPatrolRoute]:
        """
        加载所有路线
        :param whitelist: 传入后 按名单筛选路线
        :param finished: 传入后 排除已经完成的路线
        :param target_planet: 传入后 筛选相同星球的路线
        :param target_region: 传入后 筛选相同区域的路线 忽略楼层
        :return:
        """
        # 需要排除的部分
        finished_unique_id = [] if finished is None else finished

        route_list: List[WorldPatrolRoute] = []

        for planet in self.map_data.planet_list:
            planet_dir = self.get_planet_route_dir(planet)

            for route_filename in os.listdir(planet_dir):
                if not route_filename.endswith('.yml'):
                    continue

                route_path = os.path.join(planet_dir, route_filename)
                yaml_op = YamlOperator(route_path)

                planet_name = yaml_op.get('planet', None)
                region_name = yaml_op.get('region', None)
                floor = yaml_op.get('floor', None)
                tp_name = yaml_op.get('tp', None)

                planet = self.map_data.best_match_planet_by_name(planet_name)
                if planet is None:
                    log.error(f'路线 {route_filename} 无法匹配星球')
                    continue

                if target_planet is not None and target_planet.np_id != planet.np_id:
                    continue

                region = self.map_data.best_match_region_by_name(region_name, planet, target_floor=floor)
                if region is None:
                    log.error(f'路线 {route_filename} 无法匹配区域')
                    continue

                if target_region is not None and target_region.pr_id != region.pr_id:
                    continue

                tp = self.map_data.best_match_sp_by_name(region, gt(tp_name, 'ocr'))
                if tp is None:
                    log.error(f'路线 {route_filename} 无法匹配传送点')
                    continue

                route = WorldPatrolRoute(tp, yaml_op.data, route_path)
                route_id = route.unique_id

                if route_id in finished_unique_id:
                    continue

                if whitelist is not None:
                    if whitelist.type == 'white' and route_id not in whitelist.list:
                        continue
                    if whitelist.type == 'black' and route_id in whitelist.list:
                        continue

                route_list.append(route)

        log.info('最终加载 %d 条线路 过滤已完成 %d 条 使用名单 %s',
                 len(route_list), len(finished_unique_id), 'None' if whitelist is None else whitelist.name)

        return route_list

    @staticmethod
    def get_planet_route_dir(planet: Planet) -> str:
        """
        获取星球的路线文件夹目录
        :param planet:
        :return:
        """
        return os_utils.get_path_under_work_dir('config', 'world_patrol', planet.np_id)


    def get_new_route_path(self, tp: SpecialPoint) -> str:
        """
        获取新路线的文件路径
        """
        existed_route_list = self.load_all_route(target_region=tp.region)
        max_route_idx: int = 0
        for route in existed_route_list:
            max_route_idx = max(max_route_idx, route.route_num)

        planet_dir = self.get_planet_route_dir(tp.planet)
        route_filename = f'{tp.region.r_id}_R{(max_route_idx + 1):02d}_${tp.id}.yml'
        route_path = os.path.join(planet_dir, route_filename)
        return route_path

    def create_new_route(self, tp: SpecialPoint, author: str) -> WorldPatrolRoute:
        """
        根据传送点 创建一条路线
        :param tp:
        :return:
        """
        route_path = self.get_new_route_path(tp)
        return WorldPatrolRoute(tp, {
            'author': [author],
            'route': []
        }, route_path)

    def save_route(self, route: WorldPatrolRoute, author: str):
        """
        保存路线
        """
        planet_dir = self.get_planet_route_dir(route.tp.planet)
        route_filename = f'{route.tp.region.r_id}_R{route.route_num:02d}_${route.tp.id}.yml'
        route_path = os.path.join(planet_dir, route_filename)

        if route.yml_file_path != route_path:
            route.delete()
            route.yml_file_path = self.get_new_route_path(route.tp)
            route.init_route_num()

        route.save()
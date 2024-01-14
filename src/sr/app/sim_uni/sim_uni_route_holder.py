import os
from typing import List, Optional

from cv2.typing import MatLike

from basic import Rect
from basic.img import MatchResult, cv2_utils
from sr.sim_uni.sim_uni_const import SimUniLevelType

from sr.sim_uni.sim_uni_route import SimUniRoute


class SimUniRouteHolder:

    def __init__(self):
        self.uni_2_route_list: dict[str, List[SimUniRoute]] = {}
        """宇宙对用的路线配置列表 key为第几宇宙第几层"""

    def get_route_list(self, uni_num: int, level_type: SimUniLevelType) -> List[SimUniRoute]:
        """
        获取宇宙对用的路线配置列表
        :param uni_num: 第几宇宙
    :param level_type: 楼层类型
        :return:
        """
        key = '%02d-%s' % (uni_num, level_type.type_id)
        if key in self.uni_2_route_list:
            return self.uni_2_route_list[key]

        arr = []
        base_dir = SimUniRoute.get_uni_base_dir(uni_num, level_type.type_id)
        for sub in os.listdir(base_dir):
            sub_dir = os.path.join(base_dir, sub)
            if not os.path.isdir(sub_dir):
                continue
            arr.append(SimUniRoute(uni_num, level_type, int(sub)))

        self.uni_2_route_list[key] = arr
        return arr

    def clear_cache(self):
        self.uni_2_route_list.clear()


_sim_uni_route_holder: Optional[SimUniRouteHolder] = None


def get_sim_uni_route_list(uni_num: int, level_type: SimUniLevelType) -> List[SimUniRoute]:
    global _sim_uni_route_holder
    if _sim_uni_route_holder is None:
        _sim_uni_route_holder = SimUniRouteHolder()
    return _sim_uni_route_holder.get_route_list(uni_num, level_type)


def clear_sim_uni_route_cache():
    if _sim_uni_route_holder is not None:
        _sim_uni_route_holder.clear_cache()


def match_best_sim_uni_route(uni_num: int, level_type: SimUniLevelType, mm: MatLike) -> Optional[SimUniRoute]:
    """
    根据开始点的小地图的截图 找到最合适的路线
    :param uni_num: 第几宇宙
    :param level_type: 楼层类型
    :param mm: 开始点的小地图截图
    :return:
    """
    route_list = get_sim_uni_route_list(uni_num, level_type)
    target_route: Optional[SimUniRoute] = None
    target_mr: Optional[MatchResult] = None

    for route in route_list:
        source = route.mm
        template, _ = cv2_utils.crop_image(mm, Rect(50, 50, 150, 150))
        mr = cv2_utils.match_template(source, template, threshold=0.6, only_best=True)

        if mr.max is None:
            continue

        if target_route is None or target_mr.confidence < mr.max.confidence:
            target_route = route
            target_mr = mr.max

    return target_route

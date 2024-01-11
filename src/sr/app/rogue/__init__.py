import os
from typing import Optional, List

from sr.operation.combine.sim_uni import SimUniRoute


class SimUniRouteHolder:

    def __init__(self):
        self.uni_2_route_list: dict[str, List[SimUniRoute]] = {}
        """宇宙对用的路线配置列表 key为第几宇宙第几层"""

    def get_route_list(self, uni_num: int, level: int) -> List[SimUniRoute]:
        """
        获取宇宙对用的路线配置列表
        :param uni_num: 第几宇宙
        :param level: 第几层
        :return:
        """
        key = '%02d-%02d' % (uni_num, level)
        if key in self.uni_2_route_list:
            return self.uni_2_route_list[key]

        arr = []
        base_dir = SimUniRoute.get_uni_base_dir(uni_num, level)
        for sub in os.listdir(base_dir):
            sub_dir = os.path.join(base_dir, sub)
            if not os.path.isdir(sub_dir):
                continue
            arr.append(SimUniRoute(uni_num, level, int(sub)))

        self.uni_2_route_list[key] = arr
        return arr

    def clear_cache(self):
        self.uni_2_route_list.clear()


_sim_uni_route_holder: Optional[SimUniRouteHolder] = None


def get_sim_uni_route_list(uni_num: int, level: int) -> List[SimUniRoute]:
    global _sim_uni_route_holder
    if _sim_uni_route_holder is None:
        _sim_uni_route_holder = SimUniRouteHolder()
    return _sim_uni_route_holder.get_route_list(uni_num, level)


def clear_sim_uni_route_cache():
    if _sim_uni_route_holder is not None:
        _sim_uni_route_holder.clear_cache()
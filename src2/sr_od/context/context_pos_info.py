from typing import Optional

from one_dragon.base.geometry.point import Point
from sr_od.sr_map.sr_map_data import Planet, Region, SpecialPoint


class ContextPosInfo:

    def __init__(self):
        """
        运行上下文中的位置信息
        注释统一使用 pos_ 前缀
        """
        self.pos_planet: Optional[Planet] = None
        self.pos_region: Optional[Region] = None
        self.pos_point: Optional[Point] = None

        self.pos_lm_scale: int = 5  # 当前大地图缩放比例
        self.pos_cancel_mission_trace: bool = False  # 是否已经取消了任务追踪
        self.pos_first_cal_pos_after_fight: bool = False  # 战斗后第一次计算坐标 由于部分攻击会产生位移 这次的坐标识别允许更大范围

    def update_pos_after_tp(self, tp: SpecialPoint):
        """
        传送后 更新坐标
        :param tp: 传送点
        :return:
        """
        self.pos_planet = tp.planet
        self.pos_region = tp.region
        self.pos_point = tp.tp_pos

    def update_pos_after_move(self, pos: Point, region: Optional[Region] = None):
        """
        移动到达后更新位置
        :param pos:
        :param region:
        :return:
        """
        self.pos_point = pos
        if region is not None:
            self.pos_region = region

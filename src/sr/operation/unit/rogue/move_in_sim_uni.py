import time
from typing import Tuple, Optional, Callable

from cv2.typing import MatLike

from basic import Point
from basic.log_utils import log
from sr import cal_pos
from sr.const import game_config_const
from sr.context import Context
from sr.image.sceenshot import LargeMapInfo, MiniMapInfo, large_map, mini_map
from sr.operation import OperationResult
from sr.operation.unit.move_directly import MoveDirectly


class MoveDirectlyInSimUni(MoveDirectly):
    """
    从当前位置 朝目标点直线前行
    有简单的脱困功能

    模拟宇宙专用
    - 不需要考虑特殊点
    - 不需要考虑多层地图
    """
    def __init__(self, ctx: Context, lm_info: LargeMapInfo,
                 start: Point, target: Point,
                 stop_afterwards: bool = True,
                 no_run: bool = False,
                 op_callback: Optional[Callable[[OperationResult], None]] = None
                 ):
        super().__init__(ctx, lm_info,
                         start, target,
                         stop_afterwards=stop_afterwards,
                         no_run=no_run,
                         op_callback=op_callback)

    def cal_pos(self, mm: MatLike, now_time: float) -> Tuple[Optional[Point], MiniMapInfo]:
        """
        根据上一次的坐标和行进距离 计算当前位置坐标
        :param mm: 小地图截图
        :param now_time: 当前时间
        :return:
        """
        # 根据上一次的坐标和行进距离 计算当前位置
        if self.last_rec_time > 0:
            move_time = now_time - self.last_rec_time
            if move_time < 1:
                move_time = 1
        else:
            move_time = 1
        move_distance = self.ctx.controller.cal_move_distance_by_time(move_time, run=self.run_mode != game_config_const.RUN_MODE_OFF)
        last_pos = self.pos[len(self.pos) - 1]
        possible_pos = (last_pos.x, last_pos.y, move_distance)
        log.debug('准备计算人物坐标 使用上一个坐标为 %s 移动时间 %.2f 是否在移动 %s', possible_pos,
                  move_time, self.ctx.controller.is_moving)
        lm_rect = large_map.get_large_map_rect_by_pos(self.lm_info.gray.shape, mm.shape[:2], possible_pos)

        mm_info = mini_map.analyse_mini_map(mm, self.ctx.im)

        next_pos = cal_pos.cal_character_pos_for_sim_uni(self.ctx.im, self.lm_info, mm_info,
                                                         lm_rect=lm_rect, running=self.ctx.controller.is_moving)
        if next_pos is None:
            log.error('无法判断当前人物坐标 使用上一个坐标为 %s 移动时间 %.2f 是否在移动 %s', possible_pos, move_time,
                      self.ctx.controller.is_moving)
        return next_pos, mm_info

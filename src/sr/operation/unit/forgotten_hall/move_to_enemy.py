import time
from typing import Optional, Union

import cv2
import numpy as np
from cv2.typing import MatLike

from basic import Point, cal_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from sr import cal_pos
from sr.config import game_config
from sr.const import game_config_const
from sr.context import Context
from sr.image.sceenshot import mini_map
from sr.operation import Operation, OperationOneRoundResult


class MoveToEnemy(Operation):

    def __init__(self, ctx: Context, no_run: bool = False, timeout_seconds: float = 600):
        """
        需要先在忘却之庭节点内
        按小地图上的红色点 向敌人移动
        :param ctx: 上下文
        :param no_run: 不能疾跑
        :param timeout_seconds: 超时时间
        """
        super().__init__(ctx, op_name=gt('忘却之庭 向敌人移动', 'ui'), timeout_seconds=timeout_seconds)
        self.run_mode = game_config_const.RUN_MODE_OFF if no_run else game_config.get().run_mode
        self.last_move_time: float = 0  # 上一次移动的时间

    def _init_before_execute(self):
        super()._init_before_execute()
        self.last_move_time = 0

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()
        mm = mini_map.cut_mini_map(screen)
        pos = self._find_enemy_pos(mm)
        center = Point(mm.shape[1] // 2, mm.shape[0] // 2)

        if pos is None or cal_utils.distance_between(pos, center) < 10:  # 已经到达
            self.ctx.controller.stop_moving_forward()
            return Operation.round_success()
        elif pos is not None:  # 朝目标走去
            now = time.time()
            if now - self.last_move_time > 0.5:  # 隔一段时间再调整方向移动
                self.last_enemy_pos = pos
                _, _, angle = mini_map.analyse_arrow_and_angle(mm, self.ctx.im)
                self.ctx.controller.move_towards(center, pos, angle,
                                                 run=self.run_mode == game_config_const.RUN_MODE_BTN)
            return Operation.round_wait()
        else:  # 不应该有这种情况
            return Operation.round_retry('unknown')

    def _find_enemy_pos(self, mm: Optional[MatLike] = None) -> Optional[Point]:
        """
        在小地图上找到敌人红点的位置
        目前只能处理一个红点的情况
        :param mm: 小地图图片
        :return: 红点位置
        """
        if mm is None:
            screen = self.screenshot()
            mm = mini_map.cut_mini_map(screen)

        _, _, angle = mini_map.analyse_arrow_and_angle(mm, self.ctx.im)
        to_del = cal_pos.get_radio_to_del(self.ctx.im, angle)

        mm2 = mini_map.remove_radio(mm, to_del)
        # cv2_utils.show_image(mm2, win_name='mm2')

        lower_color = np.array([0, 0, 150], dtype=np.uint8)
        upper_color = np.array([60, 60, 255], dtype=np.uint8)
        red_part = cv2.inRange(mm2, lower_color, upper_color)
        # cv2_utils.show_image(red_part, win_name='red_part')

        # 膨胀一下找连通块
        to_check = cv2_utils.dilate(red_part, 5)
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(to_check, connectivity=8)

        if num_labels <= 1:  # 没有连通块 走到敌人附近了
            return None

        # 找到最大的连通区域
        largest_label = 1
        max_area = stats[largest_label, cv2.CC_STAT_AREA]
        for label in range(2, num_labels):
            area = stats[label, cv2.CC_STAT_AREA]
            if area > max_area:
                max_area = area
                largest_label = label

        # 找到最大连通区域的中心点
        center_x = int(centroids[largest_label, 0])
        center_y = int(centroids[largest_label, 1])

        return Point(center_x, center_y)

    def on_pause(self):
        super().on_pause()
        self.ctx.stop_running()
import time

import numpy as np
from cv2.typing import MatLike

from basic.i18_utils import gt
from basic.log_utils import log
from sr.app.application_base import Application
from sr.config.game_config import GameConfig, MiniMapPos
from sr.const import map_const
from sr.const.map_const import TransportPoint
from sr.context.context import Context
from sr.image.sceenshot import mini_map
from sr.operation import StateOperationNode, OperationOneRoundResult
from sr.operation.combine.transport import Transport


class Calibrator(Application):
    """
    首次运行需要的校准
    """

    def __init__(self, ctx: Context):
        super().__init__(ctx, op_name='校准')

    def add_edges_and_nodes(self) -> None:
        """
        初始化前 添加边和节点 由子类实行
        :return:
        """
        nodes = [
            StateOperationNode('传送1', op=Transport(self.ctx, map_const.P01_R02_SP02), wait_after_op=1),
            StateOperationNode('小地图定位校准', self.check_mini_map_pos),
            StateOperationNode('传送2', op=Transport(self.ctx, map_const.P01_R01_SP03), wait_after_op=1),
            StateOperationNode('转向校准', self.check_turning_rate)
        ]

        self.param_node_list = nodes

    def check_mini_map_pos(self) -> OperationOneRoundResult:
        log.info('[小地图定位校准] 开始')
        screenshot = self.screenshot()
        mm_pos: MiniMapPos = mini_map.cal_little_map_pos(screenshot)
        cfg: GameConfig = self.ctx.game_config
        cfg.update('mini_map', {
            'x': mm_pos.x,
            'y': mm_pos.y,
            'r': mm_pos.r
        })
        cfg.save()

        log.info('[小地图定位校准] 完成 位置: (%d, %d) 半径: %d', mm_pos.x, mm_pos.y, mm_pos.r)
        return self.round_success(wait=0.5)

    def check_turning_rate(self) -> OperationOneRoundResult:
        """
        检测转向 需要找一个最容易检测到见箭头的位置
        通过固定滑动距离 判断转动角度
        反推转动角度所需的滑动距离
        :return:
        """
        log.info('[转向校准] 开始')
        turn_distance = 500

        angle = self._get_current_angle()
        turn_angle = []
        for _ in range(10):
            self.ctx.controller.turn_by_distance(turn_distance)
            time.sleep(1)
            next_angle = self._get_current_angle()
            if angle is not None:
                ta = next_angle - angle if next_angle >= angle else next_angle - angle + 360
                turn_angle.append(ta)
            angle = next_angle

        avg_turn_angle = np.mean(turn_angle)
        log.info('平均旋转角度 %.4f', avg_turn_angle)
        ans = float(turn_distance / avg_turn_angle)
        log.info('每度移动距离 %.4f', ans)
        gc: GameConfig = self.ctx.game_config
        gc.update('turn_dx', ans)
        gc.save()
        log.info('[转向校准] 完成')
        # cv2.waitKey(0)
        return self.round_success(wait=0.5)

    def _get_current_angle(self):
        self.ctx.controller.move('w')
        time.sleep(1)
        screen = self.screenshot()
        mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
        center_arrow_mask, arrow_mask, next_angle = mini_map.analyse_arrow_and_angle(mm)
        log.info('当前角度 %.2f', next_angle)
        return next_angle

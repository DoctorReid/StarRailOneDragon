import time

import numpy as np
from cv2.typing import MatLike

from basic.i18_utils import gt
from basic.log_utils import log
from sr import constants
from sr.app import Application
from sr.config import game_config
from sr.config.game_config import GameConfig, MiniMapPos
from sr.constants.map import TransportPoint
from sr.context import Context, get_context
from sr.image.sceenshot import mini_map
from sr.operation.combine.transport import Transport


class Calibrator(Application):
    """
    首次运行需要的校准
    """

    def __init__(self, ctx: Context):
        super().__init__(ctx)

    def run(self):
        self._check_mini_map_pos()
        self._check_turning_rate()
        return True

    def _check_mini_map_pos(self, screenshot: MatLike = None):
        log.info('[小地图定位校准] 开始')
        if screenshot is None:
            tp: TransportPoint = constants.map.P01_R02_SP02
            op = Transport(self.ctx, tp, True)
            if not op.execute():
                log.error('传送到 %s %s 失败 小地图定位校准 失败', gt(tp.region.cn), gt(tp.cn))
                return False

            screenshot = self.screenshot()
        mm_pos: MiniMapPos = mini_map.cal_little_map_pos(screenshot)
        config: GameConfig = game_config.get()
        config.update('mini_map', {
            'x': mm_pos.x,
            'y': mm_pos.y,
            'r': mm_pos.r
        })
        config.write_config()

        log.info('[小地图定位校准] 完成 位置: (%d, %d) 半径: %d', mm_pos.x, mm_pos.y, mm_pos.r)
        return True

    def _check_turning_rate(self, tp: bool = True):
        """
        检测转向 需要找一个最容易检测到见箭头的位置
        通过固定滑动距离 判断转动角度
        反推转动角度所需的滑动距离
        :param tp: 是否需要传送
        :return:
        """
        log.info('[转向校准] 开始')
        if tp:
            p: TransportPoint = constants.map.P01_R01_SP03
            op = Transport(self.ctx, p, False)
            if not op.execute():
                log.error('传送到 %s %s 失败 转向校准 失败', gt(p.region.cn), gt(p.cn))
                return False
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
        config: GameConfig = game_config.get()
        config.update('turn_dx', ans)
        config.write_config()
        log.info('[转向校准] 完成')
        # cv2.waitKey(0)
        return ans

    def _get_current_angle(self):
        self.ctx.controller.move('w')
        time.sleep(1)
        screen = self.screenshot()
        mm = mini_map.cut_mini_map(screen)
        center_arrow_mask, arrow_mask, next_angle = mini_map.analyse_arrow_and_angle(mm, self.ctx.im)
        log.info('当前角度 %.2f', next_angle)
        return next_angle


if __name__ == '__main__':
    ctx = get_context()
    ctx.running = True
    ctx.controller.init()
    app = Calibrator(ctx)
    app.execute()
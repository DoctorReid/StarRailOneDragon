import time

import numpy as np
from cv2.typing import MatLike

from basic import cal_utils, Point, Rect
from basic.i18_utils import gt
from basic.log_utils import log
from sr import cal_pos
from sr.app import Application
from sr.config import game_config
from sr.config.game_config import GameConfig, MiniMapPos
from sr.const import map_const
from sr.const.map_const import TransportPoint
from sr.context import Context, get_context
from sr.image.sceenshot import mini_map, large_map, LargeMapInfo, MiniMapInfo
from sr.operation.combine.transport import Transport


class Calibrator(Application):
    """
    首次运行需要的校准
    """

    def __init__(self, ctx: Context):
        super().__init__(ctx)

    def _execute_one_round(self):
        self._check_mini_map_pos()
        self._check_turning_rate()
        # self._check_running_distance()
        return True

    def _check_mini_map_pos(self, screenshot: MatLike = None, config=None):
        log.info('[小地图定位校准] 开始')
        if screenshot is None:
            tp: TransportPoint = map_const.P01_R02_SP02
            op = Transport(self.ctx, tp, True)
            if not op.execute():
                log.error('传送到 %s %s 失败 小地图定位校准 失败', gt(tp.region.cn, 'ocr'), gt(tp.cn, 'ocr'))
                return False

            screenshot = self.screenshot()
        mm_pos: MiniMapPos = mini_map.cal_little_map_pos(screenshot)
        cfg: GameConfig = game_config.get()
        cfg.update('mini_map', {
            'x': mm_pos.x,
            'y': mm_pos.y,
            'r': mm_pos.r
        })
        cfg.write_config()

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
            p: TransportPoint = map_const.P01_R01_SP03
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
        gc: GameConfig = game_config.get()
        gc.update('turn_dx', ans)
        gc.write_config()
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

    def _check_running_distance(self) -> bool:
        """
        检测疾跑距离 传送到 黑塔空间站-支援舱段-月台
        应该只跑一次提供一个默认值给大家用就够了 暂时不需要用户自己校准
        :return:
        """
        log.info('疾跑距离校准 开始')
        tp: TransportPoint = map_const.P01_R04_SP02
        op = Transport(self.ctx, tp, True)
        if not op.execute():
            log.error('传送到 %s %s 失败 疾跑距离校准 失败', gt(tp.region.cn, 'ocr'), gt(tp.cn, 'ocr'))
            return False

        lm_info: LargeMapInfo = self.ctx.ih.get_large_map(tp.region)

        self.ctx.controller.start_moving_forward(run=True)

        dis_arr = []
        use_time_arr = []
        last_pos = tp.lm_pos
        last_record_time = 0

        while True:
            now_time = time.time()
            screen = self.ctx.controller.screenshot()
            mm = mini_map.cut_mini_map(screen)

            lx, ly = last_pos.x, last_pos.y
            move_distance = self.ctx.controller.cal_move_distance_by_time(now_time - last_record_time, run=True) if last_record_time > 0 else 0
            possible_pos = (lx, ly, move_distance)
            lm_rect: Rect = large_map.get_large_map_rect_by_pos(lm_info.origin.shape[:2], mm.shape[:2], possible_pos)

            sp_map = map_const.get_sp_type_in_rect(tp.region, lm_rect)
            mm_info: MiniMapInfo = mini_map.analyse_mini_map(mm, self.ctx.im, sp_types=set(sp_map.keys()))
            current_pos: Point = cal_pos.cal_character_pos(self.ctx.im, lm_info, mm_info, lm_rect, retry_without_rect=False, running=True)

            if current_pos is None:
                log.error('判断坐标失败')
                continue

            if last_record_time > 0:
                dis_arr.append(cal_utils.distance_between(last_pos, current_pos))
                use_time_arr.append(now_time - last_record_time)

            last_pos = current_pos
            last_record_time = now_time

            if len(dis_arr) > 10:
                break

        run_speed = np.sum(dis_arr) / np.sum(use_time_arr)
        log.info('疾跑平均速度 %.4f', run_speed)


if __name__ == '__main__':
    ctx = get_context()
    ctx.running = True
    ctx.controller.init()
    app = Calibrator(ctx)
    app.execute()
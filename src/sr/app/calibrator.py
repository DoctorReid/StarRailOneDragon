import math
import time

import numpy as np
from cv2.typing import MatLike

import sr
from basic.img import cv2_utils
from basic.log_utils import log
from sr import constants
from sr.app import Application
from sr.config.game_config import GameConfig, get_game_config
from sr.context import Context
from sr.control import GameController
from sr.image.sceenshot import mini_map
from sr.map_cal import MapCalculator


class Calibrator(Application):
    """
    首次运行需要的校准
    """

    def __init__(self, ctx: Context):
        self.ctx: Context = ctx
        self.ctrl: GameController = ctx.controller
        self.mc: MapCalculator = ctx.map_cal

    def run(self):
        self.ctx.running = True
        self.ctrl.init()
        screen = self.ctrl.screenshot()
        self._check_mini_map_pos(screen)

    def _check_mini_map_pos(self, screenshot: MatLike = None):
        # TODO 后续确保当前位置在基座舱段
        log.info('[小地图定位校准] 开始')
        if screenshot is None:
            screenshot = self.ctrl.screenshot()
        self.mc.cal_little_map_pos(screenshot)
        config: GameConfig = get_game_config()
        config.update('mini_map', {
            'x': self.mc.mm_pos.x,
            'y': self.mc.mm_pos.y,
            'r': self.mc.mm_pos.r
        })
        config.write_config()

        log.info('[小地图定位校准] 完成 位置: (%d, %d) 半径: %d', self.mc.mm_pos.x, self.mc.mm_pos.y, self.mc.mm_pos.r)

    def _check_turning_rate(self):
        """
        检测转向 需要找一个最容易检测到见箭头的位置
        通过固定滑动距离 判断转动角度
        反推转动角度所需的滑动距离
        :return:
        """
        turn_distance = 1000

        angle = None
        turn_angle = []
        for _ in range(5):
            self.ctrl.move('w')
            time.sleep(1)
            screen = self.ctrl.screenshot()
            mm = self.mc.cut_mini_map(screen)
            center_arrow_mask, arrow_mask, next_angle = mini_map.analyse_arrow_and_angle(mm, self.ctx.im)
            cv2_utils.show_image(center_arrow_mask, win_name='center_arrow_mask')
            cv2_utils.show_image(arrow_mask, win_name='arrow_mask')
            if angle is not None:
                ta = next_angle - angle if next_angle >= angle else next_angle - angle + 360
                turn_angle.append(ta)
            angle = next_angle
            self.ctrl.turn_by_distance(turn_distance)
            time.sleep(0.5)
        avg_turn_angle = np.mean(turn_angle)
        print(avg_turn_angle)
        config: GameConfig = get_game_config()
        config.update('turn_dx', float(turn_distance / avg_turn_angle))
        config.write_config()
        # cv2.waitKey(0)

    def _check_move_distance(self, save_screenshot: bool = False):
        pos = []
        large_map = sr.read_map_image(constants.PLANET_1_KZJ, constants.REGION_2_JZCD, 'usage')

        k = 's'
        for i in range(4):
            screen = gui_utils.screenshot_win(self.win)
            if save_screenshot:
                basic.img.get.save_debug_image(screen)
            little_map = self.mc.cut_mini_map(screen)
            x, y = self.mc.cal_character_pos_by_match(little_map, large_map, show=True)
            print(x, y)
            pos.append((x, y))
            gui_utils.key_down(k, 1)
            if i != 'q':
                time.sleep(6)

        for i in range(len(pos) - 1):
            dis = math.sqrt((pos[i+1][0] - pos[i][0])**2 + (pos[i+1][1] - pos[i][1])**2)
            print(dis)

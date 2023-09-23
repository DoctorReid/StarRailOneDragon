import math
import time

from pygetwindow import Win32Window

import dev
import sr
from basic import gui_utils
from sr import constants
from sr.config import ConfigHolder
from sr.map_cal import MapCalculator


class Calibrator:

    def __init__(self, win: Win32Window, ch: ConfigHolder, mc: MapCalculator):
        self.win: Win32Window = win
        self.ch: ConfigHolder = ch
        self.mc: MapCalculator = mc

    def check_all(self):
        # TODO 后续确保当前位置在基座舱段
        self._check_little_map_pos()

    def _check_little_map_pos(self):
        screen = gui_utils.screenshot_win(self.win)
        self.mc.cal_little_map_pos(screen)
        self.ch.update_config('game', 'little_map',
                              {'x': self.mc.map_pos.x, 'y': self.mc.map_pos.y, 'r': self.mc.map_pos.r})

    def _check_move_distance(self, save_screenshot: bool = False):
        pos = []
        large_map = sr.read_map_image(constants.PLANET_1_KZJ, constants.REGION_2_JZCD, 'usage')

        k = 's'
        for i in range(4):
            screen = gui_utils.screenshot_win(self.win)
            if save_screenshot:
                dev.save_debug_image(screen)
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

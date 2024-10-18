import time

import ctypes
from typing import Optional, ClassVar

from one_dragon.base.controller.pc_controller_base import PcControllerBase
from one_dragon.base.geometry.point import Point
from one_dragon.utils.log_utils import log
from sr_od.config.game_config import GameConfig


class SrPcController(PcControllerBase):

    MOVE_INTERACT_TYPE: ClassVar[int] = 0
    TALK_INTERACT_TYPE: ClassVar[int] = 1

    def __init__(self, game_config: GameConfig,
                 win_title: str,
                 standard_width: int = 1920,
                 standard_height: int = 1080):
        PcControllerBase.__init__(self,
                                  win_title=win_title,
                                  standard_width=standard_width,
                                  standard_height=standard_height)

        self.game_config: GameConfig = game_config
        self.turn_dx: float = self.game_config.get('turn_dx')
        self.run_speed: float = 30
        self.is_moving: bool = False
        self.is_running: bool = False  # 是否在疾跑
        self.start_move_time: float = 0

    def esc(self) -> bool:
        self.btn_controller.tap(self.game_config.key_esc)
        return True

    def open_map(self) -> bool:
        self.btn_controller.tap(self.game_config.key_open_map)
        return True

    def turn_by_distance(self, d: float):
        """
        横向转向 按距离转
        :param d: 正数往右转 人物角度增加；负数往左转 人物角度减少
        :return:
        """
        ctypes.windll.user32.mouse_event(PcControllerBase.MOUSEEVENTF_MOVE, int(d), 0)

    def move(self, direction: str, press_time: float = 0, run: bool = False):
        """
        往固定方向移动
        :param direction: 方向 wsad
        :param press_time: 持续秒数
        :param run: 是否启用疾跑
        :return:
        """
        if direction not in ['w', 's', 'a', 'd']:
            log.error('非法的方向移动 %s', direction)
            return False
        self.start_move_time = time.time()
        if press_time > 0:
            self.btn_controller.press(direction)
            self.is_moving = True
            self.enter_running(run)
            time.sleep(press_time)
            self.btn_controller.release(direction)
            self.stop_moving_forward()
        else:
            self.btn_controller.tap(direction)
        return True

    def enter_running(self, run: bool):
        """
        进入疾跑模式
        :param run: 是否进入疾跑
        :return:
        """
        if run and not self.is_running:
            time.sleep(0.02)
            self.btn_controller.tap('mouse_right')
            self.is_running = True
        elif not run and self.is_running:
            time.sleep(0.02)
            self.btn_controller.tap('mouse_right')
            self.is_running = False

    def start_moving_forward(self, run: bool = False):
        """
        开始往前走
        :param run: 是否启用疾跑
        :return:
        """
        self.is_moving = True
        self.btn_controller.press('w')
        self.enter_running(run)

    def stop_moving_forward(self):
        if not self.is_moving:
            return
        self.btn_controller.release('w')
        self.is_moving = False
        self.is_running = False

    def switch_character(self, idx: int):
        """
        切换角色
        :param idx: 第几位角色 从1开始
        :return:
        """
        log.info('切换角色 %s', str(idx))
        self.btn_controller.tap(str(idx))

    def initiate_attack(self):
        """
        主动发起攻击
        :return:
        """
        # 虽然在大世界指定坐标点击没有用 但这可以防止准备攻击时候被怪攻击 导致鼠标可以点到游戏窗口外
        self.click(Point(self.standard_width // 2, self.standard_height // 2))

    def interact(self, pos: Optional[Point] = None, interact_type: int = 0) -> bool:
        """
        交互
        :param pos: 如果是模拟器的话 需要传入交互内容的坐标
        :param interact_type: 交互类型
        :return:
        """
        if interact_type == SrPcController.MOVE_INTERACT_TYPE:
            self.btn_controller.tap(self.game_config.key_interact)
        else:
            self.click(pos)
        return True

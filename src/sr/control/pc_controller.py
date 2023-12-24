import ctypes
import time

import cv2
import pyautogui
from cv2.typing import MatLike

from basic import win_utils, Point
from basic.log_utils import log
from sr import const
from sr.config import game_config
from sr.config.game_config import GameConfig
from sr.control import GameController
from sr.image.ocr_matcher import OcrMatcher
from sr.win import Window, WinRect


class PcController(GameController):

    MOUSEEVENTF_MOVE = 0x0001
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004

    def __init__(self, win: Window, ocr: OcrMatcher):
        super().__init__(ocr)
        self.win: Window = win
        self.gc: GameConfig = game_config.get()
        self.turn_dx: float = self.gc.get('turn_dx')
        self.run_speed: float = self.gc.get('run_speed')
        self.walk_speed: float = self.gc.get('walk_speed')
        self.is_moving: bool = False
        self.is_running: bool = False  # 是否在疾跑

    def init(self):
        self.win.active()
        time.sleep(0.5)

    def esc(self) -> bool:
        pyautogui.press(self.gc.key_esc)
        return True

    def open_map(self) -> bool:
        pyautogui.press(self.gc.key_open_map)
        return True

    def click(self, pos: Point = None, press_time: float = 0) -> bool:
        """
        点击位置
        :param pos: 游戏中的位置 (x,y)
        :param press_time: 大于0时长按若干秒
        :return: 不在窗口区域时不点击 返回False
        """
        click_pos: Point
        if pos is not None:
            click_pos: Point = self.win.game2win_pos(pos)
            if click_pos is None:
                log.error('点击非游戏窗口区域 (%s)', pos)
                return False
        else:
            point: pyautogui.Point = pyautogui.position()
            click_pos = Point(point.x, point.y)

        win_utils.click(click_pos, press_time=press_time)
        return True

    def screenshot(self) -> MatLike:
        """
        截图 如果分辨率和默认不一样则进行缩放
        :return: 截图
        """
        rect: WinRect = self.win.get_win_rect()
        pyautogui.moveTo(rect.x + 50, rect.y + rect.h - 30)  # 移动到uid位置
        img = win_utils.screenshot(rect.x, rect.y, rect.w, rect.h)
        result = cv2.resize(img, (const.STANDARD_RESOLUTION_W, const.STANDARD_RESOLUTION_H)) if rect.is_scale() else img
        return result

    def scroll(self, down: int, pos: Point = None):
        """
        向下滚动
        :param down: 负数时为相上滚动
        :param pos: 滚动位置 默认分辨率下的游戏窗口里的坐标
        :return:
        """
        if pos is None:
            pos = win_utils.get_current_mouse_pos()
        win_pos = self.win.game2win_pos(pos)
        # pyautogui.scroll(down, x=win_pos[0], y=win_pos[1])
        win_utils.scroll(down, win_pos)

    def drag_to(self, end: Point, start: Point = None, duration: float = 0.5):
        """
        按住拖拽
        :param end: 拖拽目的点
        :param start: 拖拽开始点
        :param duration: 拖拽持续时间
        :return:
        """
        from_pos: Point
        if start is None:
            from_pos = win_utils.get_current_mouse_pos()
        else:
            from_pos = self.win.game2win_pos(start)

        to_pos = self.win.game2win_pos(end)
        win_utils.drag_mouse(from_pos, to_pos, duration=duration)

    def turn_by_distance(self, d: float):
        """
        横向转向 按距离转
        :param d: 正数往右转 人物角度增加；负数往左转 人物角度减少
        :return:
        """
        ctypes.windll.user32.mouse_event(PcController.MOUSEEVENTF_MOVE, int(d), 0)

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
        if press_time > 0:
            pyautogui.keyDown(direction)
            self.is_moving = True
            self.enter_running(run)
            time.sleep(press_time)
            pyautogui.keyUp(direction)
            self.is_moving = False
            self.is_running = False
        else:
            pyautogui.press(direction)
        return True

    def start_moving_forward(self, run: bool = False):
        """
        开始往前走
        :param run: 是否启用疾跑
        :return:
        """
        self.is_moving = True
        pyautogui.keyDown('w')
        self.enter_running(run)

    def stop_moving_forward(self):
        pyautogui.keyUp('w')
        self.is_moving = False
        self.is_running = False

    def initiate_attack(self):
        """
        主动发起攻击
        :return:
        """
        ctypes.windll.user32.mouse_event(PcController.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        ctypes.windll.user32.mouse_event(PcController.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    def interact(self, pos: Point, interact_type: int = 0) -> bool:
        """
        交互
        :param pos: 如果是模拟器的话 需要传入交互内容的坐标
        :param interact_type: 交互类型
        :return:
        """
        if interact_type == GameController.MOVE_INTERACT_TYPE:
            pyautogui.press(self.gc.key_interact)
        else:
            self.click(pos)
        return True

    def enter_running(self, run: bool):
        """
        进入疾跑模式
        :param run: 是否进入疾跑
        :return:
        """
        if run and not self.is_running:
            time.sleep(0.02)
            win_utils.click(primary=False)
            self.is_running = True
        elif not run and self.is_running:
            time.sleep(0.02)
            win_utils.click(primary=False)
            self.is_running = False

    def switch_character(self, idx: int):
        """
        切换角色
        :param idx: 第几位角色 从1开始
        :return:
        """
        log.info('切换角色 %s', str(idx))
        pyautogui.press(str(idx))

    def use_technique(self):
        """
        使用秘技
        :return:
        """
        log.info('使用秘技')
        pyautogui.press(self.gc.key_technique)

    def close_game(self):
        """
        关闭游戏
        :return:
        """
        try:
            self.win.win.close()
            log.info('关闭游戏成功')
        except:
            log.error('关闭游戏失败', exc_info=True)

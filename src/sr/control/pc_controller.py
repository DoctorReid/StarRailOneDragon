import ctypes
import time

import cv2
import pyautogui
from cv2.typing import MatLike

from basic import win_utils
from basic.log_utils import log
from sr.config.game_config import GameConfig, get_game_config
from sr.control import GameController
from sr.image import OcrMatcher
from sr.win import Window, WinRect


class PcController(GameController):

    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004

    def __init__(self, win: Window, ocr: OcrMatcher):
        self.win: Window = win
        self.ocr: OcrMatcher = ocr
        config: GameConfig = get_game_config()
        self.turn_dx: float = config.get('turn_dx')
        self.walk_speed: float = config.get('walk_speed')
        self.is_moving: bool = False

    def init(self):
        self.win.active()
        time.sleep(0.5)

    def esc(self) -> bool:
        pyautogui.press('esc')
        return True

    def open_map(self) -> bool:
        pyautogui.press('m')
        return True

    def click(self, pos: tuple = None, press_time: int = 0) -> bool:
        """
        点击位置
        :param pos: 游戏中的位置 (x,y)
        :param press_time: 大于0时长按若干秒
        :return: 不在窗口区域时不点击 返回False
        """
        if pos is not None:
            x, y = self.win.game2win_pos(pos)
            if x is None or y is None:
                log.error('点击非游戏窗口区域 (%s)', pos)
                return False
        else:
            point: pyautogui.Point = pyautogui.position()
            x, y = point.x, point.y

        win_utils.click(x, y, press_time=press_time)
        return True

    def screenshot(self) -> MatLike:
        """
        截图 如果分辨率和默认不一样则进行缩放
        :return: 截图
        """
        rect: WinRect = self.win.get_win_rect()
        pyautogui.moveTo(rect.x + 10, rect.y + rect.h - 10)  # 移动到uid位置
        img = win_utils.screenshot(rect.x, rect.y, rect.w, rect.h)
        return cv2.resize(img, (img.shape[0] // rect.ys, img.shape[1] // rect.xs)) if rect.is_scale() else img

    def scroll(self, down: int, pos: tuple = None):
        """
        向下滚动
        :param down: 负数时为相上滚动
        :param pos: 滚动位置 默认分辨率下的游戏窗口里的坐标
        :return:
        """
        win_pos = self.win.game2win_pos(pos) if pos is not None else (None, None)
        pyautogui.moveTo(x=win_pos[0], y=win_pos[1])
        pyautogui.scroll(down, x=win_pos[0], y=win_pos[1])

    def drag_to(self, end: tuple, start: tuple = None, duration: float = 0.5):
        """
        按住拖拽
        :param end: 拖拽目的点
        :param start: 拖拽开始点
        :param duration: 拖拽持续时间
        :return:
        """
        if start is None:
            pos = pyautogui.position()
            from_pos = (pos.x, pos.y)
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
        ctypes.windll.user32.mouse_event(0x0001, int(d), 0)

    def move(self, direction: str, press_time: int = 0):
        """
        往固定方向移动
        :param direction: 方向 wsad
        :param press_time: 持续秒数
        :return:
        """
        if direction not in ['w', 's', 'a', 'd']:
            log.error('非法的方向移动 %s', direction)
            return False
        if press_time > 0:
            self.is_moving = True
            win_utils.key_down(direction, press_time)
            self.is_moving = False
        else:
            pyautogui.press(direction)
        return True

    def start_moving_forward(self):
        """
        开始往前走
        :return:
        """
        self.is_moving = True
        pyautogui.keyDown('w')

    def stop_moving_forward(self):
        self.is_moving = False
        pyautogui.keyUp('w')

    def initiate_attack(self):
        """
        主动发起攻击
        :return:
        """
        ctypes.windll.user32.mouse_event(PcController.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        ctypes.windll.user32.mouse_event(PcController.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

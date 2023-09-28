import time

import cv2
import pyautogui
from cv2.typing import MatLike

from basic import win_utils
from basic.log_utils import log
from sr.control import GameController
from sr.image import OcrMatcher
from sr.win import Window, WinRect


class PcController(GameController):

    def __init__(self, win: Window, ocr: OcrMatcher):
        self.win: Window = win
        self.ocr: OcrMatcher = ocr
        # TODO 新增线程监听窗口切换

    def init(self):
        self.win.active()

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
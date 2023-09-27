import time

import cv2
import pyautogui
from cv2.typing import MatLike

from basic import win_utils
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

    def click(self, pos: tuple = None, duration: int = 0) -> bool:
        """
        点击位置
        :param pos: 游戏中的位置 (x,y)
        :param duration: 大于0时长按若干秒
        :return: 不在窗口区域时不点击 返回False
        """
        if pos is not None:
            x, y = self.win.game2win_pos(pos)
            if x is None or y is None:
                return False
        else:
            point: pyautogui.Point = pyautogui.position()
            x, y = point.x, point.y

        if duration > 0:
            pyautogui.moveTo(x, y)
            pyautogui.mouseDown()
            time.sleep(duration)
            pyautogui.mouseUp()
        else:
            pyautogui.click(x, y)
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

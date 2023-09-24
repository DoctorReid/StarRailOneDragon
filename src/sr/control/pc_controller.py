import cv2
import pyautogui
from cv2.typing import MatLike

from basic import win_utils
from sr.control import GameController
from sr.win import Window


class PcController(GameController):

    def __init__(self, win: Window):
        self.win: Window = win
        # TODO 新增线程监听窗口切换

    def init(self):
        self.win.active()

    def _is_scale(self):
        return self.win.xs != 1 or self.win.xy != 1

    def esc(self) -> bool:
        pyautogui.press('esc')
        return True

    def open_map(self) -> bool:
        pyautogui.press('m')
        return True

    def click(self, pos: tuple) -> bool:
        """
        点击位置
        :param pos: 游戏中的位置 (x,y)
        :return: 不在窗口区域时不点击 返回False
        """
        x, y = self.win.game2win_pos(pos)
        if x is None or y is None:
            return False
        pyautogui.click(x, y)
        return True

    def screenshot(self) -> MatLike:
        """
        截图 如果分辨率和默认不一样则进行缩放
        :return: 截图
        """
        pyautogui.moveTo(self.win.wx1 + 10, self.win.wy2 - 10)  # 移动到uid位置
        img = win_utils.screenshot_win(self.win.win)
        return cv2.resize(img, (img.shape[0] // self.win.ys, img.shape[1] // self.win.xs)) if self._is_scale() else img

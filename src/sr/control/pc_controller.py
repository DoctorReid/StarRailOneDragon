import cv2
import pyautogui
from pygetwindow import Win32Window

from basic import gui_utils
from sr.control import GameController


class PcController(GameController):

    def __init__(self, win: Win32Window):
        self.win = win

    def init(self):
        self.win.activate()

    def esc(self) -> bool:
        pyautogui.press('esc')
        return True

    def open_map(self) -> bool:
        pyautogui.press('m')
        return True

    def screenshot(self) -> cv2.typing.MatLike:
        return gui_utils.screenshot_win(self.win)
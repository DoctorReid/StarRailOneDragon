import ctypes
import time
from ctypes.wintypes import RECT
from typing import Union

from basic import win_utils, Point
from basic.log_utils import log
from sr import const


class WinRect:

    def __init__(self, x: int, y: int, w: int, h: int):
        # 窗口在桌面的偏移量
        self.x: int = x
        self.y: int = y

        # 窗口大小
        self.w: int = w
        self.h: int = h

        # 缩放比例
        self.xs: int = 1 if w == const.STANDARD_RESOLUTION_W else w * 1.0 / const.STANDARD_RESOLUTION_W
        self.ys: int = 1 if w == const.STANDARD_RESOLUTION_H else h * 1.0 / const.STANDARD_RESOLUTION_H

    def is_scale(self):
        return self.xs != 1 or self.ys != 1


class Window:

    def __init__(self, title: str):
        self.win = win_utils.get_win_by_name(title, active=False)
        self.hWnd = self.win._hWnd

    def is_active(self):
        """
        是否当前激活的窗口
        :return:
        """
        return self.win.isActive

    def active(self):
        """
        显示并激活当前窗口
        :return:
        """
        try:
            win_utils.active_win(self.win)
        except:
            log.error('切换到游戏窗口失败 可尝试手动切换到游戏窗口中 3秒后脚本启动', exc_info=True)
            time.sleep(3)

    def get_win_rect(self):
        """
        获取游戏窗口信息
        Win32Window 里是整个window的信息 参考源码获取里面client部分的
        :return: 游戏窗口信息
        """
        client_rect = RECT()
        ctypes.windll.user32.GetClientRect(self.hWnd, ctypes.byref(client_rect))
        left_top_pos = ctypes.wintypes.POINT(client_rect.left, client_rect.top)
        ctypes.windll.user32.ClientToScreen(self.hWnd, ctypes.byref(left_top_pos))
        return WinRect(left_top_pos.x, left_top_pos.y, client_rect.right, client_rect.bottom)

    def game_pos(self, pos: Union[tuple, Point], inner: bool = True, rect: WinRect = None) -> Point:
        """
        获取在游戏中的坐标
        :param pos: 默认分辨率下的游戏窗口里的坐标
        :param inner: 是否需要在窗口内 需要时坐标超出窗口返回 (None, None)
        :param rect: 窗口位置信息
        :return: 当前分辨率下的游戏窗口里坐标
        """
        if rect is None:
            rect = self.get_win_rect()
        if type(pos) == tuple:
            s_pos = Point(pos[0] * rect.xs, pos[1] * rect.ys)
        else:
            s_pos = Point(pos.x * rect.xs, pos.y * rect.ys)
        return None if inner and not self._check_game_pos(s_pos, rect) else s_pos

    def _check_game_pos(self, s_pos: Point, rect: WinRect = None):
        """
        判断游戏中坐标是否在游戏窗口内
        :param s_pos: 游戏中坐标 已经缩放
        :param rect: 窗口位置信息
        :return: 是否在游戏窗口内
        """
        if rect is None:
            rect = self.get_win_rect()
        return 0 <= s_pos.x <= rect.w and 0 <= s_pos.y <= rect.h

    def game2win_pos(self, pos: Point, inner: bool = True, rect: WinRect = None) -> Point:
        """
        获取在屏幕中的坐标
        :param pos: 默认分辨率下的游戏窗口里的坐标
        :param inner: 是否需要在屏幕内 需要时坐标超出屏幕返回 (None, None)
        :param rect: 窗口位置信息
        :return: 当前分辨率下的屏幕中的坐标
        """
        if rect is None:
            rect = self.get_win_rect()
        gp: Point = self.game_pos(pos, inner=inner, rect=rect)
        # 缺少一个屏幕边界判断 游戏窗口拖动后可能会超出整个屏幕
        return Point(rect.x + gp.x, rect.y + gp.y) if gp is not None else None

    def get_dpi(self):
        return ctypes.windll.user32.GetDpiForWindow(self.hWnd)

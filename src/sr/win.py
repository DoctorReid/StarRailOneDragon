import ctypes
from ctypes.wintypes import RECT

from basic import win_utils


class WinRect:

    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y

        self.w = w
        self.h = h

        self.xs = 1  # 缩放比例 窗口宽度 / 1980
        self.ys = 1  # 缩放比例 窗口高度 / 1080

    def is_scale(self):
        return self.xs != 1 or self.ys != 1


class Window:

    def __init__(self, title: str):
        self.win = win_utils.get_win_by_name(title, active=False)

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
        self.win.show()
        self.win.activate()

    def get_win_rect(self):
        """
        获取游戏窗口信息
        Win32Window 里是整个window的信息 参考源码获取里面client部分的
        :return: 游戏窗口信息
        """
        client_rect = RECT()
        ctypes.windll.user32.GetClientRect(self.win._hWnd, ctypes.byref(client_rect))
        left_top_pos = ctypes.wintypes.POINT(client_rect.left, client_rect.top)
        ctypes.windll.user32.ClientToScreen(self.win._hWnd, ctypes.byref(left_top_pos))
        return WinRect(left_top_pos.x, left_top_pos.y, client_rect.right, client_rect.bottom)

    def game_pos(self, pos: tuple, inner: bool = True, rect: WinRect = None):
        """
        获取在游戏中的坐标
        :param pos: 默认分辨率下的游戏窗口里的坐标
        :param inner: 是否需要在窗口内 需要时坐标超出窗口返回 (None, None)
        :param rect: 窗口位置信息
        :return: 当前分辨率下的游戏窗口里坐标
        """
        if rect is None:
            rect = self.get_win_rect()
        s_pos = (pos[0] * rect.xs, pos[1] * rect.ys)
        return (None, None) if inner and not self._check_game_pos(s_pos, rect) else s_pos

    def _check_game_pos(self, s_pos: tuple, rect: WinRect = None):
        """
        判断游戏中坐标是否在游戏窗口内
        :param s_pos: 游戏中坐标 已经缩放
        :param rect: 窗口位置信息
        :return: 是否在游戏窗口内
        """
        if rect is None:
            rect = self.get_win_rect()
        return 0 <= s_pos[0] <= rect.w and 0 <= s_pos[1] <= rect.h

    def game2win_pos(self, pos: tuple, inner: bool = True, rect: WinRect = None):
        """
        获取在屏幕中的坐标
        :param pos: 默认分辨率下的游戏窗口里的坐标
        :param inner: 是否需要在屏幕内 需要时坐标超出屏幕返回 (None, None)
        :param rect: 窗口位置信息
        :return: 当前分辨率下的屏幕中的坐标
        """
        if rect is None:
            rect = self.get_win_rect()
        gp = self.game_pos(pos, inner=inner, rect=rect)
        # TODO 缺少一个屏幕边界判断 游戏窗口拖动后可能会超出整个屏幕
        return (rect.x + gp[0], rect.y + gp[1]) if gp[0] is not None else (None, None)

    def get_dpi(self):
        return ctypes.windll.user32.GetDpiForWindow(self.win._hWnd)
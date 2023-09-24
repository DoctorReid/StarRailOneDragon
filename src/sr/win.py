from basic import win_utils


class Window:

    def __init__(self, title: str):
        self.win = win_utils.get_win_by_name(title, active=False)
        self.wx1 = self.win.left
        self.wy1 = self.win.top
        self.wx2 = self.win.right
        self.wy2 = self.win.bottom
        self.w = self.win.width
        self.h = self.win.height

        self.gcx = self.w // 2  # 游戏里的中心点
        self.gcy = self.h // 2

        self.xs = 1  # 缩放比例 窗口宽度 / 1980
        self.ys = 1  # 缩放比例 窗口高度 / 1080

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

    def game_pos(self, pos: tuple, inner: bool = True):
        """
        获取在游戏中的坐标
        :param pos: 默认分辨率下的游戏窗口里的坐标
        :param inner: 是否需要在窗口内 需要时坐标超出窗口返回 (None, None)
        :return: 当前分辨率下的游戏窗口里坐标
        """
        s_pos = (pos[0] * self.xs, pos[1] * self.ys)
        return (None, None) if inner and not self._check_game_pos(s_pos) else s_pos

    def _check_game_pos(self, s_pos: tuple):
        """
        判断游戏中坐标是否在游戏窗口内
        :param s_pos: 游戏中坐标 已经缩放
        :return: 是否在游戏窗口内
        """
        return 0 <= s_pos[0] <= self.w and 0 <= s_pos[1] <= self.h

    def game2win_pos(self, pos: tuple, inner: bool = True):
        """
        获取在屏幕中的坐标
        :param pos: 默认分辨率下的游戏窗口里的坐标
        :param inner: 是否需要在屏幕内 需要时坐标超出屏幕返回 (None, None)
        :return: 当前分辨率下的屏幕中的坐标
        """
        gp = self.game_pos(pos, inner=inner)

        # TODO 缺少一个屏幕边界判断 游戏窗口拖动后可能会超出整个屏幕
        return (self.wx1 + gp[0], self.wx2 + gp[1]) if gp[0] is not None else (None, None)


import time

from sr.app import get_context, Context
from sr.control import GameController
from sr.operation import Operation


class OpenMap(Operation):

    def __init__(self):
        """
        通过按 esc 和 m 打开大地图
        """
        pass

    def inner_exe(self, goal: dict = None) -> bool:
        ctx: Context = get_context()
        ctrl: GameController = ctx.controller
        try_times = 0

        while ctx.running and try_times < 10:
            try_times += 1
            m = ctrl.open_map()
            if not m:
                time.sleep(0.5)
                continue
            screen = ctrl.screenshot()
            if self.in_large_map(screen):
                return True
            esc = ctrl.esc()
            time.sleep(1)

        return False

    def in_large_map(self, screen):
        """
        判断是否在大地图页面了
        :param screen:
        :return:
        """
        return False
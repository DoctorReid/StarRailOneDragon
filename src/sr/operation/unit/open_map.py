import time

from sr.context import Context
from sr.image.sceenshot import large_map
from sr.operation import Operation


class OpenMap(Operation):

    def __init__(self, ctx: Context):
        """
        通过按 esc 和 m 打开大地图
        """
        self.ctx = ctx
        self.ctrl = ctx.controller
        self.ocr = ctx.ocr

    def exe(self) -> bool:
        try_times = 0

        while self.ctx.running and try_times < 10:
            try_times += 1
            m = self.ctrl.open_map()
            if not m:
                time.sleep(0.5)
                continue
            screen = self.ctrl.screenshot()
            if large_map.get_planet_name(screen, self.ocr) is not None:  # 左上角找到星球名字的化 证明在在大地图页面了
                return True
            self.ctrl.esc()
            time.sleep(1)

        return False
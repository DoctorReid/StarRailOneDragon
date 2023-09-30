import time

from basic.log_utils import log
from sr.context import Context
from sr.control import GameController
from sr.image import OcrMatcher
from sr.image.sceenshot import large_map
from sr.operation import Operation


class OpenMap(Operation):

    def __init__(self, ctx: Context):
        """
        通过按 esc 和 m 打开大地图
        """
        self.ctx = ctx

    def execute(self) -> bool:
        ctrl: GameController = self.ctx.controller
        ocr: OcrMatcher = self.ctx.ocr
        try_times = 0

        while self.ctx.running and try_times < 10:
            if not self.ctx.running:
                return False
            try_times += 1
            screen = ctrl.screenshot()
            planet = large_map.get_planet(screen, ocr)
            log.info('当前大地图所处星球 %s', planet)
            if planet is not None:  # 左上角找到星球名字的化 证明在在大地图页面了
                return True
            if try_times % 2 == 1:
                log.info('尝试打开地图')
                ctrl.open_map()
            else:
                log.info('尝试返回上级页面')
                ctrl.esc()
            time.sleep(1)

        return False

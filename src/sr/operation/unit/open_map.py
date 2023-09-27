import time

from basic.log_utils import log
from sr.context import Context, get_context
from sr.control import GameController
from sr.image import OcrMatcher
from sr.image.sceenshot import large_map
from sr.operation import Operation


class OpenMap(Operation):

    def __init__(self):
        """
        通过按 esc 和 m 打开大地图
        """
        pass

    def execute(self) -> bool:
        ctx: Context = get_context()
        ctrl: GameController = ctx.controller
        ocr: OcrMatcher = ctx.ocr
        try_times = 0

        while ctx.running and try_times < 10:
            try_times += 1
            m = ctrl.open_map()
            time.sleep(1)
            if not m:
                continue
            screen = ctrl.screenshot()
            planet = large_map.get_planet(screen, ocr)
            log.info('当前大地图所处星球 %s', planet)
            if planet is not None:  # 左上角找到星球名字的化 证明在在大地图页面了
                return True
            ctrl.esc()
            time.sleep(1)

        return False

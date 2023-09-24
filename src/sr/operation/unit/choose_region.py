import time

from sr.app import Context, get_context
from sr.control import GameController
from sr.image.sceenshot import large_map
from sr.operation import Operation


class ChooseRegion(Operation):

    def __init__(self, planet: str, region: str):
        self.planet = planet
        self.region = region
        self.scroll_distance = 200

    def inner_exe(self) -> bool:
        ctx: Context = get_context()
        ctrl: GameController = ctx.controller
        try_times = 0

        while ctx.running and try_times < 10:
            try_times += 1
            screen = ctrl.screenshot()
            planet = large_map.get_planet_name(screen, ctx.ocr)
            if planet is None or planet != self.planet:
                return False  # 目前不在目标大地图了

            find = ctrl.click_ocr(screen, self.region)  # TODO 限制一下右边的区域
            if not find:  # 向下滚动5次 再向上滚动5次
                if try_times <= 5:
                    ctrl.scroll(self.scroll_distance)  # TODO 限制一下右边的区域
                elif try_times == 5:
                    for i in range(try_times):  # 回到原点
                        ctrl.scroll(-self.scroll_distance)
                        time.sleep(1)
                    ctrl.scroll(-self.scroll_distance)
                else:
                    ctrl.scroll(-self.scroll_distance)
                time.sleep(1)

        return False

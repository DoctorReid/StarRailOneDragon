import time

from basic.i18_utils import gt
from sr.context import Context, get_context
from sr.control import GameController
from sr.image.sceenshot import large_map
from sr.operation import Operation


class ChoosePlanet(Operation):

    def __init__(self, planet: str):
        """
        在大地图页面 选择到对应的星球
        :param planet:
        """
        self.planet = planet

    def inner_exe(self) -> bool:
        ctx: Context = get_context()
        ctrl: GameController = ctx.controller
        try_times = 0

        while ctx.running and try_times < 10:
            try_times += 1
            screen = ctrl.screenshot()
            planet = large_map.get_planet_name(screen, ctx.ocr)
            if planet is not None and planet == self.planet:
                return True

            if planet is not None:
                ctrl.click_ocr(gt(''))
                time.sleep(1)
                continue
            else:
                ctrl.click_ocr(gt(''))
                time.sleep(1)
                continue

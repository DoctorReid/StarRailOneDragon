import time

from basic.i18_utils import gt
from basic.log_utils import log
from sr.context import Context
from sr.control import GameController
from sr.image.ocr_matcher import OcrMatcher
from sr.image.sceenshot import large_map, battle
from sr.operation import Operation
from sr.operation.unit.enter_auto_fight import EnterAutoFight


class OpenMap(Operation):

    def __init__(self, ctx: Context):
        """
        通过按 esc 和 m 打开大地图
        """
        super().__init__(ctx, 10, op_name=gt('打开地图', 'ui'))

    def _execute_one_round(self) -> int:
        ctrl: GameController = self.ctx.controller
        ocr: OcrMatcher = self.ctx.ocr

        screen = self.screenshot()

        battle_status = battle.get_battle_status(screen, self.ctx.im)
        if battle_status == battle.IN_WORLD:  # 主界面
            log.info('尝试打开地图')
            ctrl.open_map()
            time.sleep(2)
            return Operation.WAIT

        if battle_status == battle.BATTLING:  # 可能是路线末尾被袭击了 等待最后一次战斗结束
            fight = EnterAutoFight(self.ctx)
            fight.execute()
            return Operation.WAIT

        planet = large_map.get_planet(screen, ocr)
        log.info('当前大地图所处星球 %s', planet)
        if planet is not None:  # 左上角找到星球名字的话 证明在在大地图页面了
            return Operation.SUCCESS

        # 其他情况都需要通过返回上级菜单再尝试打开大地图
        log.info('尝试返回上级菜单')
        ctrl.esc()
        time.sleep(2)
        return Operation.RETRY

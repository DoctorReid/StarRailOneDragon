import time

from basic.log_utils import log
from sr.context import Context
from sr.image.sceenshot import battle
from sr.operation import Operation


class EnableAutoFight(Operation):
    """
    启动自动战斗和二倍速 确保执行时已进入战斗状态
    """

    def __init__(self, ctx: Context):
        super().__init__(ctx, 5)

    def run(self) -> int:
        screen = self.ctx.controller.screenshot()
        bs = battle.get_battle_status(screen, self.ctx.im)
        if battle.BATTLING != bs:  # 非战斗状态
            return Operation.SUCCESS

        if not battle.is_auto_battle_on(screen, self.ctx.im):
            log.info('检测到未启动自动战斗')
            r = battle.match_battle_ctrl(screen, self.ctx.im, 'battle_ctrl_02', is_on=False)
            if r is not None:
                log.info('启动自动战斗')
                self.ctx.controller.click((r.cx, r.cy))
                time.sleep(0.5)
            return Operation.RETRY

        if not battle.is_fast_battle_on(screen, self.ctx.im):
            log.info('检测到未启动二倍速战斗')
            r = battle.match_battle_ctrl(screen, self.ctx.im, 'battle_ctrl_03', is_on=False)
            if r is not None:
                log.info('启动二倍速战斗')
                self.ctx.controller.click((r.cx, r.cy))
                time.sleep(0.5)
            return Operation.RETRY

        return Operation.SUCCESS

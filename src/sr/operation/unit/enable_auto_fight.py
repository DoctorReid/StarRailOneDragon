import time

from basic import os_utils
from basic.i18_utils import gt
from basic.img.os import save_debug_image
from basic.log_utils import log
from sr.context.context import Context
from sr.image.sceenshot import battle, fill_uid_black, screen_state
from sr.operation import Operation


class EnableAutoFight(Operation):
    """
    启动自动战斗和二倍速 确保执行时已进入战斗状态
    """

    def __init__(self, ctx: Context):
        super().__init__(ctx, 5, op_name=gt('打开自动战斗', 'ui'))

    def _execute_one_round(self) -> int:
        screen = self.screenshot()
        if screen_state.is_normal_in_world(screen, self.ctx.im):  # 非战斗状态
            return Operation.SUCCESS

        if not battle.is_auto_battle_on(screen, self.ctx.im):
            log.info('检测到未启动自动战斗')
            if os_utils.is_debug():
                fill_uid_black(screen)
                save_debug_image(screen, prefix='no_auto')
            r = battle.match_battle_ctrl(screen, self.ctx.im, 'battle_ctrl_02', is_on=False)
            if r is not None:
                log.info('启动自动战斗')
                self.ctx.controller.click(r.center)
                time.sleep(0.5)
            return Operation.RETRY

        if not battle.is_fast_battle_on(screen, self.ctx.im):
            log.info('检测到未启动二倍速战斗')
            if os_utils.is_debug():
                fill_uid_black(screen)
                save_debug_image(screen, prefix='no_fast')
            r = battle.match_battle_ctrl(screen, self.ctx.im, 'battle_ctrl_03', is_on=False)
            if r is not None:
                log.info('启动二倍速战斗')
                self.ctx.controller.click(r.center)
                time.sleep(0.5)
            return Operation.RETRY

        return Operation.SUCCESS

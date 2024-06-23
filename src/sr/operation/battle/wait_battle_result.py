from typing import ClassVar

from basic.i18_utils import gt
from sr.context.context import Context
from sr.image.sceenshot import screen_state
from sr.operation import Operation, OperationOneRoundResult
from sr.screen_area.screen_battle import ScreenBattle
from sr.screen_area.screen_normal_world import ScreenNormalWorld


class WaitBattleResult(Operation):

    STATUS_SUCCESS: ClassVar[str] = '挑战成功'
    STATUS_FAIL: ClassVar[str] = '战斗失败'
    STATUS_NO_BATTLE: ClassVar[str] = '未进入战斗'

    def __init__(self, ctx: Context, try_attack: bool = False):
        super().__init__(ctx, op_name=gt('等待战斗结果', 'ui'))

        self.try_attack: bool = try_attack
        """未进入战斗时 是否尝试攻击"""

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        state = screen_state.get_tp_battle_screen_state(screen, self.ctx.im, self.ctx.ocr,
                                                        battle_success=True,
                                                        battle_fail=True,
                                                        in_world=True
                                                        )
        if state == ScreenBattle.AFTER_BATTLE_FAIL_1.value.status:
            return self.round_success(WaitBattleResult.STATUS_FAIL)
        elif state == ScreenBattle.AFTER_BATTLE_SUCCESS_1.value.status:
            return self.round_success(WaitBattleResult.STATUS_SUCCESS)
        elif state == ScreenNormalWorld.CHARACTER_ICON.value.status:
            if self.try_attack:
                self.ctx.controller.initiate_attack()
            return self.round_retry(wait_round_time=1)
        else:
            return self.round_wait('等待战斗结束', wait=1)

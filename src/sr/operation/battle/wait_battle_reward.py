from cv2.typing import MatLike

from basic.i18_utils import gt
from sr.context import Context
from sr.image.sceenshot import screen_state
from sr.operation import Operation, OperationOneRoundResult


class WaitBattleReward(Operation):

    """
    需要已经在进入战斗了才能用
    等待战斗结束领取奖励的页面 - 出现【挑战成功】或【挑战失败】
    """

    def __init__(self, ctx: Context, timeout_seconds: int = 1200):
        super().__init__(ctx, try_times=3, op_name=gt('等待战斗结束领取奖励', 'ui'),
                         timeout_seconds=timeout_seconds)
        self.timeout_seconds: int = timeout_seconds

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen: MatLike = self.screenshot()

        state = screen_state.get_tp_battle_screen_state(screen, self.ctx.im, self.ctx.ocr,
                                                        in_world=True,
                                                        battle_success=True,
                                                        battle_fail=True)
        if state == screen_state.ScreenState.BATTLE.value:
            return self.round_wait(wait=1)
        else:
            return self.round_success(state)

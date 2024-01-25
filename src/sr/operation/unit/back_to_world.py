from cv2.typing import MatLike

from basic.i18_utils import gt
from sr.context import Context
from sr.image.sceenshot import battle
from sr.operation import Operation, OperationOneRoundResult


class BackToWorld(Operation):

    """
    回到主界面 右上角有角色图标
    """

    def __init__(self, ctx: Context):
        super().__init__(ctx, try_times=5, op_name=gt('回到主界面', 'ui'))

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen: MatLike = self.screenshot()

        if battle.IN_WORLD == battle.get_battle_status(screen, self.ctx.im):
            return Operation.round_success()

        self.ctx.controller.esc()
        return Operation.round_retry(wait=1)

import time

from basic.i18_utils import gt
from sr.context import Context
from sr.image.sceenshot import battle
from sr.operation import Operation


class StartFight(Operation):
    """
    空地上攻击 尝试发动攻击
    """

    def __init__(self, ctx: Context):
        super().__init__(ctx, op_name=gt('主动攻击进入战斗', 'ui'), timeout_seconds=10)

    def _init_before_execute(self):
        super()._init_before_execute()

    def _execute_one_round(self) -> int:
        screen = self.screenshot()

        now_time = time.time()
        screen_status = battle.get_battle_status(screen, self.ctx.im)
        if screen_status != battle.IN_WORLD:  # 在战斗界面
            return Operation.SUCCESS

        self.ctx.controller.initiate_attack()  # 主动攻击
        time.sleep(0.5)

        return Operation.WAIT


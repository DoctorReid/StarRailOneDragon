from typing import Optional

import sr.image.sceenshot.screen_state_enum
from basic.i18_utils import gt
from sr.context import Context
from sr.image.sceenshot import screen_state
from sr.operation import Operation, OperationOneRoundResult
from sr.sim_uni.op.sim_uni_choose_bless import SimUniChooseBless
from sr.sim_uni.op.sim_uni_choose_curio import SimUniChooseCurio
from sr.sim_uni.sim_uni_challenge_config import SimUniChallengeConfig


class SimUniWaitLevelStart(Operation):

    def __init__(self, ctx: Context,
                 config: Optional[SimUniChallengeConfig] = None,
                 wait_after_success: Optional[int] = None
                 ):
        """
        模拟宇宙 等待某一层的开始
        :param ctx:
        :param priority: 优先级
        :param wait_after_success: 进入后等待秒数
        """
        super().__init__(ctx, try_times=20,
                         op_name='%s %s' %
                                 (gt('模拟宇宙', 'ui'),
                                  gt('等待楼层加载', 'ui'))
                         )

        self.config: Optional[SimUniChallengeConfig] = config
        self.first_bless_chosen: bool = False
        self.wait_after_success: Optional[int] = wait_after_success

    def _init_before_execute(self):
        super()._init_before_execute()
        self.first_bless_chosen = False

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        state = screen_state.get_sim_uni_screen_state(screen, self.ctx.im, self.ctx.ocr,
                                                      in_world=True,
                                                      bless=True,
                                                      curio=True
                                                      )
        if state == sr.image.sceenshot.screen_state_enum.ScreenState.NORMAL_IN_WORLD.value:
            # 移动进入下一层后 小地图会有缩放 稍微等一下方便小地图匹配
            return self.round_success(wait=self.wait_after_success)
        elif state == sr.image.sceenshot.screen_state_enum.ScreenState.SIM_BLESS.value:
            op = SimUniChooseBless(self.ctx, self.config, before_level_start=not self.first_bless_chosen)
            op_result = op.execute()
            if op_result.success:
                self.first_bless_chosen = True
                return self.round_wait(wait=1)
            else:
                return self.round_fail(status=op_result.status, data=op_result.data)
        elif state == sr.image.sceenshot.screen_state_enum.ScreenState.SIM_CURIOS.value:
            op = SimUniChooseCurio(self.ctx, self.config)
            op_result = op.execute()
            if op_result.success:
                return self.round_wait()
            else:
                return self.round_by_op(op_result)
        else:
            return self.round_retry('无法判断当前画面状态', wait=1)

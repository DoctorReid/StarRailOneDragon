from typing import Optional

from basic.i18_utils import gt
from sr.context import Context
from sr.image.sceenshot import screen_state
from sr.image.sceenshot.screen_state_enum import ScreenState
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

    def handle_init(self) -> Optional[OperationOneRoundResult]:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        可以返回初始化后判断的结果
        - 成功时跳过本指令
        - 失败时立刻返回失败
        - 不返回时正常运行本指令
        """
        self.first_bless_chosen = False

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        state = screen_state.get_sim_uni_screen_state(screen, self.ctx.im, self.ctx.ocr,
                                                      in_world=True,
                                                      bless=True,
                                                      curio=True,
                                                      sim_uni=True
                                                      )
        if state == ScreenState.NORMAL_IN_WORLD.value:
            # 移动进入下一层后 小地图会有缩放 稍微等一下方便小地图匹配
            return self.round_success(wait=self.wait_after_success)
        elif (state == ScreenState.SIM_BLESS.value
              or state == ScreenState.GUIDE_SIM_UNI.value):  # 2.3版本改了 开头会显示模拟宇宙
            op = SimUniChooseBless(self.ctx, self.config,
                                   skip_first_screen_check=True,
                                   before_level_start=not self.first_bless_chosen)
            op_result = op.execute()
            if op_result.success:
                self.first_bless_chosen = True
                return self.round_wait(wait=1)
            else:
                return self.round_fail(status=op_result.status, data=op_result.data)
        elif state == ScreenState.SIM_CURIOS.value:
            op = SimUniChooseCurio(self.ctx, self.config)
            op_result = op.execute()
            if op_result.success:
                return self.round_wait()
            else:
                return self.round_by_op(op_result)
        else:
            return self.round_retry('无法判断当前画面状态', wait=1)

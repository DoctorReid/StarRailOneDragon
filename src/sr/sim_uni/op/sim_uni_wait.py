from typing import Optional, Union, ClassVar

from basic.i18_utils import gt
from sr.context import Context
from sr.image.sceenshot import screen_state
from sr.operation import Operation, OperationOneRoundResult
from sr.sim_uni.op.sim_uni_choose_bless import SimUniChooseBless
from sr.sim_uni.op.sim_uni_choose_curio import SimUniChooseCurio
from sr.sim_uni.sim_uni_priority import SimUniBlessPriority, SimUniCurioPriority


class SimUniWaitLevelStart(Operation):

    STATUS_FINISHED: ClassVar[str] = '挑战结束'  # 已经通关了
    STATUS_START: ClassVar[str] = '楼层开始'  # 还需要挑战

    def __init__(self, ctx: Context,
                 bless_priority: Optional[SimUniBlessPriority] = None,
                 curio_priority: Optional[SimUniCurioPriority] = None,
                 wait_after_success: Optional[int] = None
                 ):
        """
        模拟宇宙 等待某一层的开始
        :param ctx:
        :param bless_priority: 祝福优先级
        :param curio_priority: 奇物优先级
        :param wait_after_success: 进入后等待秒数
        """
        super().__init__(ctx, try_times=20,
                         op_name='%s %s' %
                                 (gt('模拟宇宙', 'ui'),
                                  gt('等待楼层加载', 'ui'))
                         )

        self.bless_priority: Optional[SimUniBlessPriority] = bless_priority
        self.curio_priority: Optional[SimUniCurioPriority] = curio_priority
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
                                                      curio=True,
                                                      empty_to_close=True
                                                      )
        if state == screen_state.ScreenState.NORMAL_IN_WORLD.value:
            # 移动进入下一层后 小地图会有缩放 稍微等一下方便小地图匹配
            return Operation.round_success(SimUniWaitLevelStart.STATUS_START, wait=self.wait_after_success)
        elif state == screen_state.ScreenState.SIM_BLESS.value:
            op = SimUniChooseBless(self.ctx, self.bless_priority, before_level_start=not self.first_bless_chosen)
            op_result = op.execute()
            if op_result.success:
                self.first_bless_chosen = True
                return Operation.round_wait()
            else:
                return Operation.round_fail(status=op_result.status, data=op_result.data)
        elif state == screen_state.ScreenState.SIM_CURIOS.value:
            op = SimUniChooseCurio(self.ctx, self.curio_priority)
            op_result = op.execute()
            if op_result.success:
                return Operation.round_wait()
            else:
                return Operation.round_fail(status=op_result.status, data=op_result.data)
        elif state == screen_state.ScreenState.EMPTY_TO_CLOSE.value:
            return self._click_empty_to_continue()
        else:
            return Operation.round_retry('无法判断当前画面状态', wait=1)

    def _click_empty_to_continue(self) -> OperationOneRoundResult:
        click = self.ctx.controller.click(screen_state.TargetRect.EMPTY_TO_CLOSE.value.center)

        if click:
            return Operation.round_success()
        else:
            return Operation.round_retry('点击空白处关闭失败')

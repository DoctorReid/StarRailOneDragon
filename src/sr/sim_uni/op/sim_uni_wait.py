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
                 ):
        """
        模拟宇宙 等待某一层的开始
        :param ctx:
        :param bless_priority: 祝福优先级
        :param curio_priority: 奇物优先级
        """
        super().__init__(ctx, try_times=20,
                         op_name='%s %s' %
                                 (gt('模拟宇宙', 'ui'),
                                  gt('等待楼层加载', 'ui'))
                         )

        self.bless_priority: Optional[SimUniBlessPriority] = bless_priority
        self.curio_priority: Optional[SimUniCurioPriority] = curio_priority

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        if screen_state.is_normal_in_world(screen, self.ctx.im):
            return Operation.round_success(SimUniWaitLevelStart.STATUS_START)

        if screen_state.in_sim_uni_choose_bless(screen, self.ctx.ocr):
            op = SimUniChooseBless(self.ctx, self.bless_priority, before_level_start=True)
            op_result = op.execute()
            if op_result.success:
                return Operation.round_wait()
            else:
                return Operation.round_fail(status=op_result.status, data=op_result.data)
        elif screen_state.in_sim_uni_choose_curio(screen, self.ctx.ocr):
            op = SimUniChooseCurio(self.ctx, self.curio_priority)
            op_result = op.execute()
            if op_result.success:
                return Operation.round_wait()
            else:
                return Operation.round_fail(status=op_result.status, data=op_result.data)
        else:
            return Operation.round_retry('无法判断当前画面状态', wait=1)

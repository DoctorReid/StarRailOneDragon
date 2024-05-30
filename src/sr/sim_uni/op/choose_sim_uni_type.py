from typing import ClassVar

from cv2.typing import MatLike

from basic import Point
from basic.i18_utils import gt
from sr.context import Context
from sr.image.sceenshot import screen_state
from sr.image.sceenshot.screen_state_enum import ScreenState
from sr.operation import Operation, OperationOneRoundResult
from sr.sim_uni.sim_uni_const import SimUniType


class ChooseSimUniType(Operation):

    SWITCH_TYPE_BTN: ClassVar[Point] = Point(242, 809)  # 还类型的按钮

    def __init__(self, ctx: Context, target: SimUniType):
        """
        需要在模拟宇宙入口页面中使用
        选择 模拟宇宙 或 拓展装置
        :param ctx:
        """

        super().__init__(ctx, try_times=5,
                         op_name='%s %s %s' % (gt('模拟宇宙', 'ui'), gt('选择类型', 'ui'), gt(target.value, 'ui')))
        self.target: SimUniType = target

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen: MatLike = self.screenshot()

        state = screen_state.get_sim_uni_initial_screen_state(screen, self.ctx.im, self.ctx.ocr)

        if state == ScreenState.SIM_TYPE_NORMAL.value:
            return self.round_success()
        elif state == ScreenState.SIM_TYPE_EXTEND.value:
            self.ctx.controller.click(ChooseSimUniType.SWITCH_TYPE_BTN)
            return self.round_wait(wait=1)
        else:
            # 有可能出现了每周第一次打开的积分奖励进度画面 随便点击一个地方关闭
            self.ctx.controller.click(screen_state.TargetRect.UI_TITLE.value.center)
            return self.round_retry('未选择对应模拟宇宙类型', wait=1)

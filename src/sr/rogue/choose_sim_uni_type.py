from typing import ClassVar

from cv2.typing import MatLike

from basic import Point
from basic.i18_utils import gt
from sr.context import Context
from sr.image.sceenshot.screen_state import in_secondary_ui, ScreenState
from sr.operation import Operation, OperationOneRoundResult
from sr.rogue import SimUniverseType


class ChooseSimUniType(Operation):

    SWITCH_TYPE_BTN: ClassVar[Point] = Point(0, 0)  # 还类型的按钮

    def __init__(self, ctx: Context, target: SimUniverseType):
        """
        需要在模拟宇宙入口页面中使用
        选择 模拟宇宙 或 拓展装置
        :param ctx:
        """

        super().__init__(ctx, try_times=5,
                         op_name='%s %s %s' % (gt('模拟宇宙', 'ui'), gt('选择类型', 'ui'), gt(target.value, 'ui')))
        self.target: SimUniverseType = target

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen: MatLike = self.screenshot()
        if in_secondary_ui(screen, self.ctx.ocr, ScreenState.SIM_TYPE_NORMAL.value):
            return Operation.round_success()

        self.ctx.controller.click(ChooseSimUniType.SWITCH_TYPE_BTN)
        return Operation.round_retry('未选择对应模拟宇宙类型', wait=1)

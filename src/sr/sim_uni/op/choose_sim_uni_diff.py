




from typing import ClassVar

from cv2.typing import MatLike

from basic import Point
from basic.i18_utils import gt
from sr.context.context import Context
from sr.image.sceenshot.screen_state import in_secondary_ui
from sr.image.sceenshot.screen_state_enum import ScreenState
from sr.operation import Operation, OperationOneRoundResult


class ChooseSimUniDiff(Operation):

    DIFF_POINT_MAP: ClassVar[dict[int, Point]] = {
        1: Point(132, 166),
        2: Point(132, 269),
        3: Point(132, 380),
        4: Point(132, 485),
        5: Point(132, 597),
    }

    def __init__(self, ctx: Context, num: int):
        """
        需要在模拟宇宙入口页面中使用 且先选择了普通模拟宇宙
        选择对应的难度
        :param ctx:
        :param num: 难度 支持 1~5
        """
        super().__init__(ctx, try_times=5,
                         op_name='%s %s %s' % (gt('模拟宇宙', 'ui'), gt('选择难度', 'ui'),
                                               gt('默认', 'ui') if num == 0 else str(num))
                         )

        self.num: int = num

    def _execute_one_round(self) -> OperationOneRoundResult:
        if self.num == 0:  # 默认难度
            return self.round_success()
        screen: MatLike = self.screenshot()

        if not in_secondary_ui(screen, self.ctx.ocr, ScreenState.SIM_TYPE_NORMAL.value):
            return self.round_retry('未在模拟宇宙页面', wait=1)

        if not self.ctx.controller.click(ChooseSimUniDiff.DIFF_POINT_MAP[self.num]):
            return self.round_retry('点击难度失败', wait=1)

        return self.round_success(wait=1)

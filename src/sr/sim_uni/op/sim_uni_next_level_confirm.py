from typing import ClassVar

from basic import Rect
from basic.i18_utils import gt
from sr.context import Context
from sr.image.sceenshot import screen_state
from sr.operation import Operation, OperationOneRoundResult


class SimUniNextLevelConfirm(Operation):

    NEXT_CONFIRM_BTN: ClassVar[Rect] = Rect(1006, 647, 1330, 697)  # 确认按钮

    def __init__(self, ctx: Context):
        """
        前往下一层时 可能需要的确认
        - 精英层有领取奖励的确认
        :param ctx:
        """
        super().__init__(ctx,
                         op_name='%s %s' %
                                 (gt('模拟宇宙', 'ui'),
                                  gt('确认进入下一层', 'ui'))
                         )

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()
        if not screen_state.is_normal_in_world(screen, self.ctx.im):
            click_confirm = self.ocr_and_click_one_line('确认', SimUniNextLevelConfirm.NEXT_CONFIRM_BTN,
                                                        screen=screen)
            if click_confirm == Operation.OCR_CLICK_SUCCESS:
                return Operation.round_success(wait=1)
            elif click_confirm == Operation.OCR_CLICK_NOT_FOUND:
                return Operation.round_success()
            else:
                return Operation.round_retry('点击确认失败', wait=0.25)
        else:
            return Operation.round_retry('在大世界页面')

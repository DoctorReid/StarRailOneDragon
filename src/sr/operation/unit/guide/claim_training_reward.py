from typing import Optional

from basic.i18_utils import gt
from sr.context import Context
from sr.image.sceenshot import phone_menu
from sr.image.sceenshot.screen_state import in_secondary_ui
from sr.operation import Operation, OperationOneRoundResult


class ClaimTrainingReward(Operation):

    def __init__(self, ctx: Context):
        """
        需要在【指南】-【每日实训】页面中使用
        获取当前实训奖励
        :param ctx: 上下文
        """
        super().__init__(
            ctx,
            op_name='%s %s' % (
                gt('每日实训', 'ui'),
                gt('获取奖励', 'ui')
            )
        )
        self.claim: bool = False

    def _init_before_execute(self):
        super()._init_before_execute()
        self.claim = False

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        if not in_secondary_ui(screen, self.ctx.ocr, '指南', lcs_percent=0.1):
            return Operation.round_retry('未在指南页面', wait=1)

        if not in_secondary_ui(screen, self.ctx.ocr, '每日实训', lcs_percent=0.1):
            return Operation.round_retry('未在每日实训页面', wait=1)

        pos = phone_menu.get_training_reward_claim_btn_pos(screen, self.ctx.im)
        if pos is None:
            return Operation.round_retry('未找到奖励按钮', wait=0.5)
        else:
            self.ctx.controller.click(pos.center)
            return Operation.round_success()

    def _retry_fail_to_success(self, retry_status: str) -> Optional[str]:
        if retry_status == '未找到奖励按钮':
            return retry_status
        else:
            return None

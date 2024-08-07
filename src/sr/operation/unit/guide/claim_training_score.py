from typing import Optional

from cv2.typing import MatLike

from basic.i18_utils import gt
from basic.img import MatchResult
from sr.context.context import Context
from sr.image.sceenshot import phone_menu
from sr.operation import Operation, OperationOneRoundResult


class ClaimTrainingScore(Operation):

    def __init__(self, ctx: Context):
        """
        需要在【指南】-【每日实训】页面使用
        点击领取按钮 把奖励都领取了
        :param ctx:
        """
        super().__init__(ctx, try_times=3,
                         op_name='%s %s' % (gt('每日实训', 'ui'), gt('领取点数', 'ui')))

        self.claim: bool = False  # 是否有领取

    def handle_init(self) -> Optional[OperationOneRoundResult]:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        可以返回初始化后判断的结果
        - 成功时跳过本指令
        - 失败时立刻返回失败
        - 不返回时正常运行本指令
        """
        self.claim = False

        return None

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen: MatLike = self.screenshot()
        result: MatchResult = phone_menu.get_training_activity_claim_btn_pos(screen, self.ctx.ocr)
        if result is None:
            return self.round_retry()
        else:
            self.ctx.controller.click(result.center)
            self.claim = True
            return self.round_wait(wait=1)

    def _retry_fail_to_success(self, retry_status: str) -> Optional[str]:
        """
        :retry_status: 重试返回的状态
        :return:
        """
        return '无可领取' if not self.claim else '领取完毕'

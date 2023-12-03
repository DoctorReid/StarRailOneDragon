import time
from typing import Optional

from cv2.typing import MatLike

from basic.i18_utils import gt
from basic.img import MatchResult
from basic.log_utils import log
from sr.app import Application, AppRunRecord, AppDescription, register_app
from sr.const import phone_menu_const
from sr.context import Context
from sr.image.sceenshot import phone_menu
from sr.operation import Operation
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu

CLAIM_TRAINING = AppDescription(cn='实训奖励', id='claim_training')
register_app(CLAIM_TRAINING)


class ClaimTrainingRecord(AppRunRecord):

    def __init__(self):
        super().__init__(CLAIM_TRAINING.id)


claim_training_record: Optional[ClaimTrainingRecord] = None


def get_record() -> ClaimTrainingRecord:
    global claim_training_record
    if claim_training_record is None:
        claim_training_record = ClaimTrainingRecord()
    return claim_training_record


class ClaimTraining(Application):

    def __init__(self, ctx: Context):
        super().__init__(ctx, op_name=gt('领取实训奖励', 'ui'),
                         run_record=get_record())
        self.phase: int = 0

    def _execute_one_round(self) -> int:
        if self.phase == 0:  # 打开菜单
            op = OpenPhoneMenu(self.ctx)
            if op.execute().success:
                self.phase += 1
                return Operation.WAIT
            else:
                return Operation.FAIL
        elif self.phase == 1:  # 检测指南红点并点击
            screen: MatLike = self.screenshot()
            result: MatchResult = phone_menu.get_phone_menu_item_pos(screen, self.ctx.im, phone_menu_const.INTERASTRAL_GUIDE, alert=True)
            if result is None:
                log.info('检测不到【指南红点】跳过')
                return Operation.SUCCESS
            else:
                self.ctx.controller.click(result.center)
                self.phase += 1
                time.sleep(1)
                return Operation.WAIT
        elif self.phase == 2:  # 检测活跃度【领取】并点击
            screen: MatLike = self.screenshot()
            result: MatchResult = phone_menu.get_training_activity_claim_btn_pos(screen, self.ctx.ocr)
            if result is None:
                log.info('活跃度领取完毕')
                self.phase += 1
                return Operation.WAIT
            else:
                self.ctx.controller.click(result.center)
                time.sleep(1)
                return Operation.WAIT
        elif self.phase == 3:  # 检测领取奖励
            screen: MatLike = self.screenshot()
            result: MatchResult = phone_menu.get_training_reward_claim_btn_pos(screen, self.ctx.im)
            if result is None:
                log.info('奖励领取完毕')
                self.phase += 1
                return Operation.WAIT
            else:
                self.ctx.controller.click(result.center)
                time.sleep(1)
                return Operation.WAIT
        elif self.phase == 4:  # 返回菜单
            op = OpenPhoneMenu(self.ctx)
            if op.execute().success:
                return Operation.SUCCESS
            else:
                return Operation.FAIL

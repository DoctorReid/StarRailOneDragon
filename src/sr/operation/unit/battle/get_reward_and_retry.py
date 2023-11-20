from cv2.typing import MatLike

from basic import str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr.context import Context
from sr.image.sceenshot import battle
from sr.operation import Operation
from sr.operation.unit.battle.click_challenge_confirm import ClickChallengeConfirm
from sr.operation.unit.battle.wait_battle_reward import WaitBattleReward


class GetRewardAndRetry(Operation):

    """
    需要已经在进入战斗了才能用
    重复挑战副本
    """

    def __init__(self, ctx: Context, run_times: int, need_confirm: bool = False,
                 success_callback=None):
        """
        :param ctx:
        :param run_times: 包含第一次，总共需要的成功次数
        :param success_callback: 每一次挑战成功的回调
        """
        super().__init__(ctx, try_times=run_times + 5, op_name=gt('领奖并重复挑战', 'ui'))
        self.run_times: int = run_times
        self.success_times: int = 0
        self.fail_times: int = 0
        self.need_confirm: bool = need_confirm
        self.success_callback = success_callback

    def _execute_one_round(self):
        wait = WaitBattleReward(self.ctx)

        if not wait.execute():
            return Operation.RETRY

        screen: MatLike = self.screenshot()
        battle_result: str = battle.get_battle_result_str(screen, self.ctx.ocr)

        if gt('挑战成功', 'ocr') == battle_result:
            log.info('副本挑战成功')
            self.success_times += 1
            if self.success_callback is not None:
                self.success_callback()
        else:
            log.info('副本挑战失败')
            self.fail_times += 1

        if self.fail_times >= 5:  # 失败太多就退出 不要浪费时间了
            return Operation.FAIL

        if self.success_times >= self.run_times:
            part, _ = cv2_utils.crop_image(screen, battle.AFTER_BATTLE_EXIT_BTN_RECT)
            ocr_result = self.ctx.ocr.ocr_for_single_line(part, strict_one_line=True)
            if str_utils.find_by_lcs(gt('退出关卡', 'ocr'), ocr_result, 0.5):
                if self.ctx.controller.click(battle.AFTER_BATTLE_EXIT_BTN_RECT.center):
                    return Operation.SUCCESS
            return Operation.RETRY
        else:
            part, _ = cv2_utils.crop_image(screen, battle.AFTER_BATTLE_CHALLENGE_AGAIN_BTN_RECT)
            ocr_result = self.ctx.ocr.ocr_for_single_line(part, strict_one_line=True)
            if str_utils.find_by_lcs(gt('再来一次', 'ocr'), ocr_result, 0.5):
                if self.ctx.controller.click(battle.AFTER_BATTLE_CHALLENGE_AGAIN_BTN_RECT.center):
                    if self.need_confirm:
                        op = ClickChallengeConfirm(self.ctx)
                        if op.execute():
                            return Operation.WAIT

        return Operation.RETRY

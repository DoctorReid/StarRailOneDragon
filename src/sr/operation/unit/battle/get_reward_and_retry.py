from cv2.typing import MatLike

from basic import str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.context import Context
from sr.image.sceenshot import battle
from sr.operation import Operation
from sr.operation.unit.battle.wait_battle_reward import WaitBattleReward


class GetRewardAndRetry(Operation):

    """
    需要已经在进入战斗了才能用
    重复挑战副本
    """

    def __init__(self, ctx: Context, run_times: int):
        """
        :param ctx:
        :param run_times: 包含第一次，总共需要的成功次数
        """
        super().__init__(ctx, try_times=run_times + 5, op_name=gt('领奖并重复挑战', 'ui'))
        self.run_times: int = run_times
        self.success_times: int = 0
        self.fail_times: int = 0

    def _execute_one_round(self):
        wait = WaitBattleReward(self.ctx)

        if not wait.execute():
            return Operation.RETRY

        screen: MatLike = self.screenshot()
        battle_result: str = battle.get_battle_result_str(screen, self.ctx.ocr)

        if str_utils.find_by_lcs(gt('挑战成功', 'ocr'), battle_result, 0.55):
            self.success_times += 1
        else:
            self.fail_times += 1

        if self.fail_times >= 5:  # 失败太多就退出 不要浪费时间了
            return Operation.FAIL

        if self.success_times >= self.run_times:
            return Operation.SUCCESS
        else:
            part, _ = cv2_utils.crop_image(screen, battle.AFTER_BATTLE_CHALLENGE_AGAIN_BTN_RECT)
            ocr_result = self.ctx.ocr.ocr_for_single_line(part, strict_one_line=True)
            if str_utils.find_by_lcs(gt('再来一次', 'ocr'), ocr_result, 0.5):
                if self.ctx.controller.click(battle.AFTER_BATTLE_CHALLENGE_AGAIN_BTN_RECT.center):
                    return Operation.WAIT

        return Operation.RETRY

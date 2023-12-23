import time
from typing import Optional, ClassVar, List

from cv2.typing import MatLike

from basic import Rect, str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr.context import Context
from sr.operation import Operation, OperationOneRoundResult
from sr.operation.unit.enable_auto_fight import EnableAutoFight
from sr.operation.unit.forgotten_hall.wait_in_node import WaitNodeStart


class AutoFightInForgottenHall(Operation):

    AFTER_BATTLE_RESULT_RECT_1: ClassVar[Rect] = Rect(820, 200, 1100, 270)  # 挑战成功 有奖励
    AFTER_BATTLE_RESULT_RECT_2: ClassVar[Rect] = Rect(820, 300, 1100, 370)  # 挑战成功 无奖励
    AFTER_BATTLE_SUCCESS_RECT_LIST: ClassVar[List[Rect]] = [AFTER_BATTLE_RESULT_RECT_1, AFTER_BATTLE_RESULT_RECT_2]
    AFTER_BATTLE_RESULT_RECT_3: ClassVar[Rect] = Rect(785, 230, 1155, 320)  # 战斗失败

    BATTLE_SUCCESS_STATUS: ClassVar[str] = '挑战成功'  # 成功 最后一个节点成功才会出现
    BATTLE_FAIL_STATUS: ClassVar[str] = '战斗失败'  # 失败 任意一个节点失败都会出现

    def __init__(self, ctx: Context, timeout_seconds: float = 600):
        """
        需要在忘却之前敌人面前使用
        主动攻击进入战斗 然后等战斗结束
        """
        super().__init__(ctx, op_name=gt('忘却之庭 进入战斗', 'ui'), timeout_seconds=timeout_seconds)
        self.with_battle: bool = False  # 是否有进入战斗
        self.last_attack_time: float = 0  # 上次攻击的时间
        self.last_in_battle_time: float = 0  # 上次在战斗时间
        self.last_check_auto_fight_time: float = 0  # 上次检测自动战斗的时间

    def _init_before_execute(self):
        super()._init_before_execute()
        self.last_in_battle_time = time.time()

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        battle_result = self._check_battle_result(screen)
        if battle_result is not None:  # 战斗失败或者最后一个节点成功了
            log.info('检测到战斗结果 %s', battle_result)
            return Operation.round_success(battle_result)

        now_time = time.time()
        part, _ = cv2_utils.crop_image(screen, WaitNodeStart.EXIT_BTN)
        match_result_list = self.ctx.im.match_template(part, 'ui_icon_10', only_best=True)
        if len(match_result_list) == 0:  # 在战斗界面
            if now_time - self.last_check_auto_fight_time > 10:
                self.last_check_auto_fight_time = now_time
                eaf = EnableAutoFight(self.ctx)
                # eaf.execute()
            time.sleep(0.5)  # 战斗部分
            self.with_battle = True
            self.last_in_battle_time = now_time
            return Operation.round_wait()

        if self.with_battle:  # 这里说明进入了下一个节点
            log.info('战斗结束')
            return Operation.round_success()

        if now_time - self.last_attack_time > 0.2:
            log.info('发起攻击')
            self.ctx.controller.initiate_attack()
            time.sleep(0.5)

        if now_time - self.last_in_battle_time > 20:
            return Operation.round_fail()

        return Operation.round_wait()

    def _check_battle_result(self, screen: Optional[MatLike] = None) -> Optional[str]:
        """
        检测战斗结果并返回
        :param screen: 屏幕截图
        :return: 战斗结果
        """
        if screen is None:
            screen = self.screenshot()

        for rect in AutoFightInForgottenHall.AFTER_BATTLE_SUCCESS_RECT_LIST:
            part, _ = cv2_utils.crop_image(screen, rect)
            ocr_result = self.ctx.ocr.ocr_for_single_line(part, strict_one_line=True)
            if str_utils.find_by_lcs(gt('挑战成功', 'ocr'), ocr_result, percent=0.3):  # 战斗过程中有可能错误识别文字 稍微提高阈值
                # cv2_utils.show_image(part, win_name='_check_battle_result')
                return AutoFightInForgottenHall.BATTLE_SUCCESS_STATUS

        part, _ = cv2_utils.crop_image(screen, AutoFightInForgottenHall.AFTER_BATTLE_RESULT_RECT_3)
        ocr_result = self.ctx.ocr.ocr_for_single_line(part, strict_one_line=True)
        if str_utils.find_by_lcs(gt('战斗失败', 'ocr'), ocr_result, percent=0.3):
            # cv2_utils.show_image(part, win_name='_check_battle_result')
            return AutoFightInForgottenHall.BATTLE_FAIL_STATUS

        return None

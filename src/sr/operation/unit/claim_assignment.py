import time

from cv2.typing import MatLike

from basic import Rect, str_utils
from basic.i18_utils import gt
from basic.img import MatchResultList, cv2_utils
from basic.log_utils import log
from sr.config import game_config
from sr.const import game_config_const
from sr.context import Context
from sr.operation import Operation


class ClaimAssignment(Operation):

    """
    完成委托
    1. 检测当前是否有【领取】按钮，有的话就点击
    2. 检测当前是否有【再次派遣】按钮，有的话就点击
    3. 都没有的情况就在上方找红点，看哪里有可以领取的

    2023-11-12 中英文最高画质测试完毕
    """

    CATEGORY_RECT = Rect(320, 190, 1200, 280)  # 上方类目
    ITEM_RECT = Rect(330, 280, 800, 860)  # 左边列表
    CLAIM_BTN_RECT = Rect(1400, 880, 1530, 920)  # 【领取】
    RESEND_BTN_RECT = Rect(1160, 930, 1290, 970)  # 【再次派遣】

    def __init__(self, ctx: Context):
        super().__init__(ctx, try_times=20, op_name=gt('完成委托', 'ui'))

    def _execute_one_round(self) -> int:
        screen: MatLike = self.screenshot()

        if self.check_claim_and_click(screen):
            return Operation.RETRY

        if self.check_resend_and_click(screen):
            return Operation.RETRY

        if self.check_alert_category_and_click(screen):
            return Operation.RETRY

        return Operation.SUCCESS

    def check_claim_and_click(self, screen: MatLike) -> bool:
        """
        检查有下方有没有【领取】按键 有的话就点击
        :param screen: 屏幕截图
        :return: 是否有
        """
        claim_btn_part, _ = cv2_utils.crop_image(screen, ClaimAssignment.CLAIM_BTN_RECT)
        ocr_result = self.ctx.ocr.ocr_for_single_line(claim_btn_part, strict_one_line=True)
        lcs_percent = 0.3 if game_config_const.LANG_CN == game_config.get().lang else 0.55
        if str_utils.find_by_lcs(gt('领取', 'ocr'), ocr_result, percent=lcs_percent):
            self.ctx.controller.click(ClaimAssignment.CLAIM_BTN_RECT.center)
            log.info('检测到【领取】 点击')
            time.sleep(1)
            return True
        return False

    def check_resend_and_click(self, screen: MatLike):
        """
        检查是否有再次派遣并点击
        :return:
        """
        resend_btn_part, _ = cv2_utils.crop_image(screen, ClaimAssignment.RESEND_BTN_RECT)
        ocr_result = self.ctx.ocr.ocr_for_single_line(resend_btn_part, strict_one_line=True)
        if str_utils.find_by_lcs(gt('再次派遣', 'ocr'), ocr_result, percent=0.3):
            self.ctx.controller.click(ClaimAssignment.RESEND_BTN_RECT.center)
            log.info('检测到【再次派遣】 点击')
            time.sleep(1)
            return True
        return False

    def check_alert_category_and_click(self, screen: MatLike) -> bool:
        """
        检测上方分类中是否有红点 有的话就点击
        :return: 是否有红点
        """

        category_part, _ = cv2_utils.crop_image(screen, ClaimAssignment.CATEGORY_RECT)
        result_list: MatchResultList = self.ctx.im.match_template(category_part, 'ui_alert')

        if len(result_list) > 0:  # 有红点
            self.ctx.controller.click(ClaimAssignment.CATEGORY_RECT.left_top + result_list.max.center)
            log.info('检测到【红点】 点击')
            time.sleep(1)
            return True

        return False



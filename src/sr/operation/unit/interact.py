import time

import cv2
import numpy as np
from cv2.typing import MatLike

from basic import Point, Rect
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr import const
from sr.context import Context
from sr.control import GameController
from sr.operation import Operation


class Interact(Operation):
    """
    移动场景的交互 即跟人物、点位交互
    """

    INTERACT_RECT = Rect(900, 400, 1450, 870)
    TRY_INTERACT_MOVE = 'sssaaawwwdddsssdddwwwaaawwwaaasssdddwwwdddsssaaa'  # 分别往四个方向绕圈

    def __init__(self, ctx: Context, cn: str, wait: int = 0):
        """
        :param ctx:
        :param cn: 需要交互的中文
        :param wait: 成功之后等待的秒数
        """
        super().__init__(ctx, try_times=len(Interact.TRY_INTERACT_MOVE), op_name=gt('交互 %s', 'ui') % gt(cn, 'ui'))
        self.cn = cn
        self.wait = wait

    def _execute_one_round(self):
        time.sleep(0.5)  # 稍微等待一下 可能交互按钮还没有出来
        screen = self.screenshot()
        return self.check_on_screen(screen)

    def check_on_screen(self, screen: MatLike) -> int:
        """
        在屏幕上找到交互内容进行交互
        :param screen: 屏幕截图
        :return: 操作结果
        """
        l = 200
        u = 255
        lower_color = np.array([l, l, l], dtype=np.uint8)
        upper_color = np.array([u, u, u], dtype=np.uint8)
        part, _ = cv2_utils.crop_image(screen, Interact.INTERACT_RECT)
        white_part = cv2.inRange(part, lower_color, upper_color)  # 提取白色部分方便匹配
        # cv2_utils.show_image(white_part, wait=0)

        ocr_result = self.ctx.ocr.match_words(white_part, words=[self.cn])

        if len(ocr_result) == 0:  # 目前没有交互按钮 尝试挪动触发交互
            self.ctx.controller.move(Interact.TRY_INTERACT_MOVE[self.op_round - 1])
            return Operation.RETRY
        else:
            for r in ocr_result.values():
                if self.ctx.controller.interact(Point(r.max.cx, r.max.cy),
                                                GameController.MOVE_INTERACT_TYPE,
                                                self.wait):
                    log.info('交互成功 %s', gt(self.cn))
                    return Operation.SUCCESS

        return Operation.RETRY


class TalkInteract(Operation):

    """
    交谈过程中的交互
    """
    INTERACT_RECT = Rect(900, 400, 1760, 870)

    def __init__(self, ctx: Context, option: str,
                 lcs_percent: float = -1,
                 conversation_seconds: int = 10):
        """

        :param ctx:
        :param option: 交谈中选择的选项
        :param lcs_percent: 使用LCS匹配的阈值
        :param conversation_seconds: 交谈最多持续的描述
        """

        super().__init__(ctx, try_times=conversation_seconds,
                         op_name=gt('交谈', 'ui') + ' ' + gt(option, 'ocr'))

        self.option: str = option
        self.lcs_percent: float = lcs_percent

    def _execute_one_round(self) -> int:
        screen: MatLike = self.screenshot()
        lower_color = np.array([200, 200, 200], dtype=np.uint8)
        upper_color = np.array([255, 255, 255], dtype=np.uint8)
        part, _ = cv2_utils.crop_image(screen, TalkInteract.INTERACT_RECT)
        white_part = cv2.inRange(part, lower_color, upper_color)  # 提取白色部分方便匹配
        # cv2_utils.show_image(white_part, wait=0)

        ocr_result = self.ctx.ocr.match_words(white_part, words=[self.option], lcs_percent=self.lcs_percent)

        if len(ocr_result) == 0:  # 目前没有交互按钮 尝试挪动触发交互
            self.ctx.controller.click(const.CLICK_TO_CONTINUE_POS)
            time.sleep(1)
            return Operation.RETRY
        else:
            for r in ocr_result.values():
                to_click: Point = r.max.center + TalkInteract.INTERACT_RECT.left_top
                if self.ctx.controller.interact(to_click, GameController.TALK_INTERACT_TYPE):
                    log.info('交互成功 %s', gt(self.option))
                    return Operation.SUCCESS

        return Operation.RETRY
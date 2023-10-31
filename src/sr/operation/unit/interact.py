import time

import cv2
import numpy as np
from cv2.typing import MatLike

from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr.context import Context
from sr.operation import Operation


class Interact(Operation):
    """
    点击交互
    """

    rect = [900, 400, 1450, 870]
    TRY_INTERACT_MOVE = 'sssaaawwwdddsssdddwwwaaawwwaaasssdddwwwdddsssaaa'  # 分别往四个方向绕圈

    def __init__(self, ctx: Context, cn: str, wait: int):
        """
        :param ctx:
        :param cn: 需要交互的中文
        :param wait: 成功之后等待的秒数
        """
        super().__init__(ctx, try_times=len(Interact.TRY_INTERACT_MOVE))
        self.cn = cn
        self.wait = wait

    def run(self):
        time.sleep(0.5)  # 稍微等待一下 可能交互按钮还没有出来
        screen = self.screenshot()
        return self.check_on_screen(screen)

    def check_on_screen(self, screen: MatLike):
        """
        在屏幕上找到交互内容进行交互
        :param screen: 屏幕截图
        :return: 操作结果
        """
        l = 200
        u = 255
        lower_color = np.array([l, l, l], dtype=np.uint8)
        upper_color = np.array([u, u, u], dtype=np.uint8)
        white_part = cv2.inRange(cv2_utils.crop_image(screen, Interact.rect)[0], lower_color, upper_color)  # 提取白色部分方便匹配
        # cv2_utils.show_image(white_part, wait=0)

        ocr_result = self.ctx.ocr.match_words(white_part, words=[self.cn])

        if len(ocr_result) == 0:  # 目前没有交互按钮 尝试挪动触发交互
            self.ctx.controller.move(Interact.TRY_INTERACT_MOVE[self.op_round])
            return Operation.RETRY
        else:
            for r in ocr_result.values():
                if self.ctx.controller.interact((r.max.cx, r.max.cy), self.wait):
                    log.info('交互成功 %s', gt(self.cn))
                    return Operation.SUCCESS

        return Operation.RETRY
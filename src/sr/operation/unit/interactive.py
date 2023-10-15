import time

import cv2
import numpy as np
from cv2.typing import MatLike

from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.context import Context
from sr.operation import Operation


class Interactive(Operation):
    """
    点击交互
    """

    rect = [900, 400, 1450, 870]

    def __init__(self, ctx: Context, cn: str, wait: int):
        """
        :param ctx:
        :param cn: 需要交互的中文
        :param wait: 成功之后等待的秒数
        """
        super().__init__(ctx, try_times=12)
        self.cn = cn
        self.wait = wait

    def run(self):
        time.sleep(0.5)  # 稍微等待一下 可能交互按钮还没有出来
        screen = self.ctx.controller.screenshot()
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
        white_part = cv2.inRange(cv2_utils.crop_image(screen, Interactive.rect), lower_color, upper_color)  # 提取白色部分方便匹配
        # cv2_utils.show_image(white_part, wait=0)

        ocr_result = self.ctx.ocr.match_words(white_part, words=[gt(self.cn)])

        if len(ocr_result) == 0:  # 目前没有交互按钮 尝试左右挪动触发交互
            move = 'wasd'
            self.ctx.controller.move(move[self.try_times % 4])
            return Operation.RETRY
        else:
            for r in ocr_result.values():
                if self.ctx.controller.interactive((r.max.cx, r.max.cy), self.wait):
                    return Operation.SUCCESS

        return Operation.RETRY
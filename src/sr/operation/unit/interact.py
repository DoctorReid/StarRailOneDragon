import time
from typing import ClassVar, Optional

import cv2
import numpy as np
from cv2.typing import MatLike

from basic import Point, Rect
from basic.i18_utils import gt
from basic.img import cv2_utils, MatchResult
from basic.log_utils import log
from sr import const
from sr.context import Context
from sr.control import GameController
from sr.operation import Operation, OperationOneRoundResult
from sr.screen_area.screen_normal_world import ScreenNormalWorld


def check_move_interact(ctx: Context, screen: MatLike, cn: str,
                        single_line: bool = False, lcs_percent: float = 0.1) -> Optional[MatchResult]:
    """
    在画面上识别是否有可交互的文本
    :param ctx: 上下文
    :param screen: 游戏画面截图
    :param cn: 需要识别的中文交互文本
    :param single_line: 是否只有单行
    :param lcs_percent: 文本匹配阈值
    :return: 返回文本位置
    """
    l = 200
    u = 255
    lower_color = np.array([l, l, l], dtype=np.uint8)
    upper_color = np.array([u, u, u], dtype=np.uint8)
    area: ScreenNormalWorld = ScreenNormalWorld.MOVE_INTERACT_SINGLE_LINE if single_line else ScreenNormalWorld.MOVE_INTERACT
    part, _ = cv2_utils.crop_image(screen, area.value.rect)
    white_part = cv2.inRange(part, lower_color, upper_color)  # 提取白色部分方便匹配
    # cv2_utils.show_image(white_part, wait=0)

    ocr_result = ctx.ocr.match_words(white_part, words=[cn], lcs_percent=lcs_percent)
    if len(ocr_result) > 0:
        for mrl in ocr_result.values():
            return mrl.max
    else:
        return None


class Interact(Operation):
    """
    移动场景的交互 即跟人物、点位交互
    """

    TRY_INTERACT_MOVE: ClassVar[str] = 'sssaaawwwdddsssdddwwwaaawwwaaasssdddwwwdddsssaaa'  # 分别往四个方向绕圈

    def __init__(self, ctx: Context, cn: str, lcs_percent: float = -1,
                 single_line: bool = False, no_move: bool = False):
        """
        :param ctx:
        :param cn: 需要交互的中文
        :param lcs_percent: ocr匹配阈值
        :param single_line: 是否确认只有一行的交互 此时可以缩小文本识别范围
        :param no_move: 不移动触发交互 适用于确保能站在交互点的情况。例如 各种体力本、模拟宇宙事件点
        """
        super().__init__(ctx, try_times=2 if no_move else len(Interact.TRY_INTERACT_MOVE),
                         op_name=gt('交互 %s', 'ui') % gt(cn, 'ui'))
        self.cn: str = cn
        self.lcs_percent: float = lcs_percent
        self.single_line: bool = single_line
        self.no_move: bool = no_move

    def _execute_one_round(self):
        time.sleep(0.5)  # 稍微等待一下 可能交互按钮还没有出来
        screen = self.screenshot()
        return self.check_on_screen(screen)

    def check_on_screen(self, screen: MatLike) -> OperationOneRoundResult:
        """
        在屏幕上找到交互内容进行交互
        :param screen: 屏幕截图
        :return: 操作结果
        """
        word_pos = check_move_interact(self.ctx, screen, self.cn,
                                       single_line=self.single_line,
                                       lcs_percent=self.lcs_percent)

        if word_pos is None:  # 目前没有交互按钮 尝试挪动触发交互
            if not self.no_move:
                self.ctx.controller.move(Interact.TRY_INTERACT_MOVE[self.op_round - 1])
            return Operation.round_retry(wait=0.25)
        else:
            if self.ctx.controller.interact(word_pos.center,
                                            GameController.MOVE_INTERACT_TYPE):
                return Operation.round_success()

        return Operation.round_retry()


class TalkInteract(Operation):

    INTERACT_RECT: ClassVar[Rect] = Rect(1292, 560, 1878, 802)

    def __init__(self, ctx: Context, option: str,
                 lcs_percent: float = -1,
                 conversation_seconds: int = 10):
        """
        交谈过程中的交互
        :param ctx:
        :param option: 交谈中选择的选项
        :param lcs_percent: 使用LCS匹配的阈值
        :param conversation_seconds: 交谈最多持续的描述
        """

        super().__init__(ctx, try_times=conversation_seconds,
                         op_name=gt('交谈', 'ui') + ' ' + gt(option, 'ocr'))

        self.option: str = option
        self.lcs_percent: float = lcs_percent

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen: MatLike = self.screenshot()
        part = cv2_utils.crop_image_only(screen, TalkInteract.INTERACT_RECT)
        # cv2_utils.show_image(part, wait=0)

        ocr_result = self.ctx.ocr.match_words(part, words=[self.option], lcs_percent=self.lcs_percent)

        if len(ocr_result) == 0:  # 目前没有交互按钮 说明当前在对话 点击继续
            self.ctx.controller.click(const.CLICK_TO_CONTINUE_POS)
            return Operation.round_retry(wait=1)
        else:
            for r in ocr_result.values():
                to_click: Point = r.max.center + TalkInteract.INTERACT_RECT.left_top
                if self.ctx.controller.interact(to_click, GameController.TALK_INTERACT_TYPE):
                    return Operation.round_success()

        return Operation.round_retry(wait=1)

import time
from typing import List

from cv2.typing import MatLike

from basic import str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils, MatchResult
from sr.context.context import Context
from sr.operation import Operation, OperationOneRoundResult
from sr.screen_area import ScreenArea
from sr.screen_area.screen_trillion_catapult import ScreenTrillionCatapult


def check_line_green(ctx, screen, lcs_percent):
    """
    检查弹珠机轨迹是否连通;;
    """
    words = get_move_interact_words(ctx, screen)
    for word in words:
        if str_utils.find_by_lcs(word.data, gt('轨迹连通', 'ocr'), percent=lcs_percent):
            return word
    return None


def get_move_interact_words(ctx: Context, screen: MatLike) -> List[MatchResult]:
    """
    获取交互文本
    :param ctx:
    :param screen:
    :param single_line:
    :return:
    """
    area: ScreenArea = ScreenTrillionCatapult.CATAPULT_SINGLE_LINE.value
    part, _ = cv2_utils.crop_image(screen, area.rect)
    # cv2_utils.show_image(white_part, wait=0)

    word = ctx.ocr.run_ocr_single_line(part)
    if word is not None:
        return [MatchResult(1, area.rect.x1, area.rect.y1, area.rect.width, area.rect.height, data=word)]
    else:
        return []


class Catapult(Operation):
    """
    弹珠机
    """

    def __init__(self, ctx: Context, lcs_percent: float = 0.1):
        """
        :param ctx:
        :param cn: 需要交互的中文
        :param lcs_percent: ocr匹配阈值
        :param single_line: 是否确认只有一行的交互 此时可以缩小文本识别范围
        :param no_move: 不移动触发交互 适用于确保能站在交互点的情况。例如 各种体力本、模拟宇宙事件点
        """
        super().__init__(ctx, try_times=2)
        self.lcs_percent: float = lcs_percent

    def check_on_screen(self, screen: MatLike) -> OperationOneRoundResult:
        """
        在屏幕上找到交互内容进行交互
        :param screen: 屏幕截图
        :return: 操作结果
        """
        word_pos = check_line_green(self.ctx, screen, lcs_percent=self.lcs_percent)
        if word_pos:
            area = ScreenTrillionCatapult.CATAPULT.value
            self.ctx.controller.click(area.center)
            return self.round_success()
        else:
            self.leave_trillion()
            return self.round_fail('连通线路被阻挡')

    def leave_trillion(self):
        area = ScreenTrillionCatapult.EXIT_BTN.value
        self.ctx.controller.click(area.center)
        time.sleep(1)
        area = ScreenTrillionCatapult.EXIT_DIALOG_CONFIRM.value
        self.ctx.controller.click(area.center)

    def _execute_one_round(self):
        time.sleep(3)  # 稍微等待一下 可能路径连线还没完成
        screen = self.screenshot()
        return self.check_on_screen(screen)

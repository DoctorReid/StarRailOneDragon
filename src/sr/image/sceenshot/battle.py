from cv2.typing import MatLike

from basic.i18_utils import gt
from sr.image import OcrMatcher

IN_WORLD = 1
ENTERING_BATTLE = 2
BATTLING = 3
ENDING_BATTLE_SUCCESS = 4
ENDING_BATTLE_FAIL = 5


def get_battle_status(screen: MatLike, ocr: OcrMatcher):
    """
    判断当天屏幕的战斗状态
    :param screen: 屏幕截图
    :param ocr: ocr
    :return: 状态
    """
    if is_tab_at_right_bottom(screen, ocr):
        return IN_WORLD


def is_tab_at_right_bottom(screen: MatLike, ocr: OcrMatcher):
    """
    右下角是否有轮盘
    :param screen: 屏幕截图
    :param ocr: ocr
    :return: 右下角是否有轮盘
    """
    part = screen[1030:, 1750:]
    result = ocr.match_words(part, words=[gt('轮盘')])
    return len(result) > 0
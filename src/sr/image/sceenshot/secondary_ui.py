"""判断二级UI的地方"""
from cv2.typing import MatLike

from basic import Rect
from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.image.ocr_matcher import OcrMatcher


class SecondaryUiTitle:

    def __init__(self, cn: str):
        self.cn: str = cn
        """标题中文"""


TITLE_GUIDE = SecondaryUiTitle(cn="星际和平指南")
TITLE_NAMELESS_HONOR = SecondaryUiTitle(cn="无名勋礼")
TITLE_FORGOTTEN_HALL = SecondaryUiTitle(cn="忘却之庭")

TITLE_INVENTORY = SecondaryUiTitle(cn="背包")

TITLE_SYNTHESIZE = SecondaryUiTitle(cn="合成")


TITLE_RECT = Rect(98, 39, 350, 100)


def in_secondary_ui(screen: MatLike, ocr: OcrMatcher,
                    title_cn: str, lcs_percent: float = 0.3) -> bool:
    """
    根据页面左上方标题文字 判断在哪个二级页面中
    :param screen: 屏幕截图
    :param ocr: OCR识别
    :param title_cn: 中文标题
    :param lcs_percent: LCS阈值
    :return:
    """
    part, _ = cv2_utils.crop_image(screen, TITLE_RECT)
    ocr_map = ocr.match_words(part, words=[gt(title_cn, 'ui')],
                              lcs_percent=lcs_percent, merge_line_distance=10)

    return len(ocr_map) > 0

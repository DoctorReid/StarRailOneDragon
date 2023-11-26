"""判断二级UI的地方"""
from cv2.typing import MatLike

from basic import Rect
from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.image.ocr_matcher import OcrMatcher


TITLE_RECT = Rect(30, 30, 220, 90)


def in_secondary_ui(screen: MatLike, ocr: OcrMatcher, title: str) -> bool:
    """
    根据页面左上方标题文字 判断在哪个二级页面中
    :param screen: 屏幕截图
    :param ocr: OCR识别
    :param title: 标题
    :return:
    """
    part, _ = cv2_utils.crop_image(screen, TITLE_RECT)
    ocr_map = ocr.match_words(part, words=[gt(title, 'ui')], lcs_percent=0.3)

    return  len(ocr_map) > 0

from cv2.typing import MatLike

from basic.img import cv2_utils
from sr.image.ocr_matcher import OcrMatcher
from sr.screen_area.screen_normal_world import ScreenNormalWorld


def pc_can_use_technique(screen: MatLike, ocr: OcrMatcher, key: str) -> bool:
    """
    PC端使用 判断当前是否可以使用秘技 - 秘技按钮上有显示快捷键
    :param screen: 屏幕棘突
    :param ocr: OCR
    :param key: 秘技按键
    :return:
    """
    area = ScreenNormalWorld.TECH_KEY.value
    part = cv2_utils.crop_image_only(screen, area.rect)
    # cv2_utils.show_image(part, win_name='pc_can_use_technique', wait=0)
    ocr_result = ocr.ocr_for_single_line(part)

    if ocr_result is not None and ocr_result.lower() == key.lower():
        return True
    else:
        return False

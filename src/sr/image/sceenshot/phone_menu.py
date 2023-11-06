from cv2.typing import MatLike

from basic import Rect, str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils, MatchResult, MatchResultList
from sr.const.phone_menu_const import PhoneMenuItem
from sr.image import ImageMatcher
from sr.image.ocr_matcher import OcrMatcher


TRAILBLAZE_LEVEL_PART = Rect(1280, 240, 1460, 270)  # 等级
MENU_ITEMS_PART = Rect(1270, 300, 1810, 1070)  # 菜单选项


def in_phone_menu(screen: MatLike, ocr: OcrMatcher) -> bool:
    """
    是否在菜单页面 有显示等级
    :param screen:
    :param ocr:
    :return:
    """
    part, _ = cv2_utils.crop_image(screen, TRAILBLAZE_LEVEL_PART)

    ocr_result: str = ocr.ocr_for_single_line(part)

    if str_utils.find_by_lcs(gt('开拓等级', 'ocr'), ocr_result, percent=0.55):
        return True

    return False


def get_phone_menu_item_pos(screen: MatLike, im: ImageMatcher, item: PhoneMenuItem) -> MatchResult:
    """
    获取菜单中某个具体选项的位置
    :param screen:
    :param im:
    :param item:
    :return:
    """
    part, _ = cv2_utils.crop_image(screen, MENU_ITEMS_PART)
    result_list: MatchResultList = im.match_template(screen, item.template_id, only_best=True)

    return result_list.max


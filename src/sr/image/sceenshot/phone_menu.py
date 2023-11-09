from cv2.typing import MatLike

from basic import Rect, str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils, MatchResult, MatchResultList
from sr.const.phone_menu_const import PhoneMenuItem
from sr.image import ImageMatcher
from sr.image.ocr_matcher import OcrMatcher


TRAILBLAZE_LEVEL_PART = Rect(1280, 240, 1460, 270)  # 等级
MENU_ITEMS_PART = Rect(1270, 300, 1810, 1070)  # 菜单选项
MENU_ITEMS_AT_RIGHT_PART = Rect(1810, 230, 1915, 1030)  # 菜单侧栏选项
ELLIPSIS_PART = Rect(1390, 50, 1810, 350)  # 省略号...的位置
SUPPORT_CHARACTER_PART = Rect(940, 140, 1700, 520)  # 支援角色的框

NAMELESS_HONOR_TAB_PART = Rect(810, 30, 1110, 100)  # 无名勋礼上方的tab
NAMELESS_HONOR_TAB_1_CLAIM_PART = Rect(1270, 890, 1530, 950)  # 无名勋礼第1个tab的一键领取按钮
NAMELESS_HONOR_TAB_2_CLAIM_PART = Rect(1520, 890, 1810, 950)  # 无名勋礼第2个tab的一键领取按钮


def in_phone_menu(screen: MatLike, ocr: OcrMatcher) -> bool:
    """
    是否在菜单页面 有显示等级
    :param screen: 屏幕截图
    :param ocr: 文字识别器
    :return:
    """
    part, _ = cv2_utils.crop_image(screen, TRAILBLAZE_LEVEL_PART)

    ocr_result: str = ocr.ocr_for_single_line(part)

    if str_utils.find_by_lcs(gt('开拓等级', 'ocr'), ocr_result, percent=0.55):
        return True

    return False


def get_phone_menu_item_pos(screen: MatLike, im: ImageMatcher, item: PhoneMenuItem, alert: bool = False) -> MatchResult:
    """
    获取菜单中某个具体选项的位置
    :param screen: 屏幕截图
    :param im: 图片匹配器
    :param item:
    :param alert: 是否有感叹号红点
    :return:
    """
    part, _ = cv2_utils.crop_image(screen, MENU_ITEMS_PART)
    result_list: MatchResultList = im.match_template(part, item.template_id, only_best=True)
    result: MatchResult = result_list.max

    if result is None:
        return None

    result.x += MENU_ITEMS_PART.x1
    result.y += MENU_ITEMS_PART.y1

    if alert:
        if is_item_with_alert(screen, im, result, (50, -50)):
            return result
        else:
            return None
    else:
        return result


def get_phone_menu_item_pos_at_right(screen: MatLike, im: ImageMatcher, item: PhoneMenuItem, alert: bool = False) -> MatchResult:
    """
    获取菜单侧栏中某个具体选项的位置
    :param screen: 屏幕截图
    :param im: 图片匹配器
    :param item:
    :param alert: 是否有感叹号红点
    :return:
    """
    part, _ = cv2_utils.crop_image(screen, MENU_ITEMS_AT_RIGHT_PART)
    result_list: MatchResultList = im.match_template(part, item.template_id, only_best=True)
    result: MatchResult = result_list.max

    if result is None:
        return None

    result.x += MENU_ITEMS_AT_RIGHT_PART.x1
    result.y += MENU_ITEMS_AT_RIGHT_PART.y1

    if alert:
        if is_item_with_alert(screen, im, result, (50, -50)):
            return result
        else:
            return None
    else:
        return result


def get_phone_menu_ellipsis_pos(screen: MatLike, im: ImageMatcher, alert: bool = False):
    """
    获取菜单上方省略号的位置
    :param screen: 屏幕截图
    :param im: 图片匹配器
    :param alert: 是否有感叹号红点
    :return:
    """
    part, _ = cv2_utils.crop_image(screen, ELLIPSIS_PART)
    cv2_utils.show_image(part, win_name='ELLIPSIS_PART')
    result_list: MatchResultList = im.match_template(part, 'ui_ellipsis', only_best=True, threshold=0.3)
    result: MatchResult = result_list.max

    if result is None:
        return None

    result.x += ELLIPSIS_PART.x1
    result.y += ELLIPSIS_PART.y1

    if alert:
        if is_item_with_alert(screen, im, result, (50, -50)):
            return result
        else:
            return None
    else:
        return result


def get_phone_menu_ellipsis_item_pos(screen: MatLike, im: ImageMatcher, ocr: OcrMatcher, item_cn: str, alert: bool = False):
    """
    获取菜单上方省略号弹出的选项位置
    :param screen: 屏幕截图
    :param im: 图片匹配器
    :param ocr: 文字识别器
    :param item_cn: 需要选择的选项中文
    :param alert: 是否有感叹号红点
    :return:
    """
    part, _ = cv2_utils.crop_image(screen, ELLIPSIS_PART)

    ocr_map = ocr.match_words(part, words=[item_cn], lcs_percent=0.55)
    if len(ocr_map) == 0:
        return None

    result: MatchResult = ocr_map.popitem()[1].max

    result.x += ELLIPSIS_PART.x1
    result.y += ELLIPSIS_PART.y1

    if alert:
        if is_item_with_alert(screen, im, result, (130, -50)):
            return result
        else:
            return None
    else:
        return result


def is_item_with_alert(screen: MatLike, im: ImageMatcher, item_result: MatchResult, offset: tuple) -> bool:
    """
    图标右上角是否有感叹号
    :param screen: 屏幕截图
    :param im: 图片匹配器
    :param item_result: 图标匹配结果
    :param offset: 感叹号在图标右上角的偏移量 x应该为正数 y应该为负数
    :return:
    """
    x1, y1 = item_result.x, item_result.y + offset[1]
    x2, y2 = item_result.x + item_result.w + offset[0], item_result.y + item_result.h
    alert_result: MatchResultList = get_alert_pos(screen, im, Rect(x1, y1, x2, y2))
    return alert_result.max is not None


def get_alert_pos(screen: MatLike, im: ImageMatcher, rect: Rect) -> MatchResultList:
    """
    获取省略号的位置
    :param screen: 屏幕截图
    :param im: 图片匹配器
    :param rect: 屏幕的特定范围
    :return: 省略号的位置
    """
    part, _ = cv2_utils.crop_image(screen, rect)
    # cv2_utils.show_image(part, win_name='get_alert_pos')
    return im.match_template(part, 'ui_alert')


def get_nameless_honor_tab_pos(screen: MatLike, im: ImageMatcher, tab: int, alert: bool = False) -> MatchResult:  # TODO 下个版本再测试红点
    """
    获取 无名勋礼 页面上方 tab图标 的位置
    :param screen: 屏幕截图
    :param im: 图片匹配器
    :param tab: 第几个tab
    :param alert: 是否有感叹号红点
    :return: tab的位置
    """
    part, _ = cv2_utils.crop_image(screen, NAMELESS_HONOR_TAB_PART)
    result_list = im.match_template(part, 'nameless_honor_%d' % tab, only_best=True)

    result: MatchResult = result_list.max

    if result is None:
        return None

    result.x += NAMELESS_HONOR_TAB_PART.x1
    result.y += NAMELESS_HONOR_TAB_PART.y1

    if alert:
        if is_item_with_alert(screen, im, result, (50, -50)):
            return result
        else:
            return None
    else:
        return result


def get_nameless_honor_tab_2_claim_pos(screen: MatLike, ocr: OcrMatcher):
    """
    获取无名勋礼第2个tab 任务的【一键领取】按钮位置
    :param screen: 屏幕截图
    :param ocr: 文字识别器
    :return:
    """
    part, _ = cv2_utils.crop_image(screen, NAMELESS_HONOR_TAB_2_CLAIM_PART)

    ocr_map = ocr.match_words(part, words=['一键领取'], lcs_percent=0.55)
    if len(ocr_map) == 0:
        return None

    result: MatchResult = ocr_map.popitem()[1].max

    result.x += NAMELESS_HONOR_TAB_2_CLAIM_PART.x1
    result.y += NAMELESS_HONOR_TAB_2_CLAIM_PART.y1

    return result


def get_nameless_honor_tab_1_claim_pos(screen: MatLike, ocr: OcrMatcher):
    """
    获取无名勋礼第2个tab 任务的【一键领取】按钮位置
    :param screen: 屏幕截图
    :param ocr: 文字识别器
    :return:
    """
    part, _ = cv2_utils.crop_image(screen, NAMELESS_HONOR_TAB_1_CLAIM_PART)

    ocr_map = ocr.match_words(part, words=['一键领取'], lcs_percent=0.55)  # TODO 下个版本测试
    if len(ocr_map) == 0:
        return None

    result: MatchResult = ocr_map.popitem()[1].max

    result.x += NAMELESS_HONOR_TAB_1_CLAIM_PART.x1
    result.y += NAMELESS_HONOR_TAB_1_CLAIM_PART.y1

    return result
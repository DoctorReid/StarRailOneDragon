from typing import Optional

import cv2
import numpy as np
from cv2.typing import MatLike

from basic import Rect, str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils, MatchResult, MatchResultList
from sr.const.phone_menu_const import PhoneMenuItem
from sr.image import ImageMatcher
from sr.image.ocr_matcher import OcrMatcher


TRAILBLAZE_LEVEL_PART = Rect(1280, 240, 1505, 275)  # 等级
MENU_ITEMS_PART = Rect(1270, 300, 1810, 1070)  # 菜单选项
MENU_ITEMS_AT_RIGHT_PART = Rect(1810, 230, 1915, 1030)  # 菜单侧栏选项
ELLIPSIS_PART = Rect(1390, 50, 1810, 350)  # 省略号...的位置
SUPPORT_CHARACTER_PART = Rect(940, 140, 1700, 520)  # 支援角色的框

NAMELESS_HONOR_TAB_PART = Rect(810, 30, 1110, 100)  # 无名勋礼上方的tab
NAMELESS_HONOR_TAB_1_CLAIM_PART = Rect(1270, 890, 1530, 950)  # 无名勋礼第1个tab的一键领取按钮
NAMELESS_HONOR_TAB_2_CLAIM_PART = Rect(1520, 890, 1810, 950)  # 无名勋礼第2个tab的一键领取按钮
NAMELESS_HONOR_TAB_1_CANCEL_BTN = Rect(620, 970, 790, 1010)  # 无名勋礼第1个tab的一键领取后的【取消】按钮

GUIDE_TRAINING_TASK_RECT = Rect(290, 470, 1560, 680)  # 指南-实训 任务框
GUIDE_TRAINING_ACTIVITY_CLAIM_RECT = Rect(270, 780, 1560, 890)  # 指南-实训 活跃度领取框
GUIDE_TRAINING_REWARD_CLAIM_RECT = Rect(420, 270, 1670, 370)  # 指南-实训 奖励领取框


def in_phone_menu(screen: MatLike, ocr: OcrMatcher) -> bool:
    """
    是否在菜单页面 有显示等级
    :param screen: 屏幕截图
    :param ocr: 文字识别器
    :return:
    """
    part, _ = cv2_utils.crop_image(screen, TRAILBLAZE_LEVEL_PART)

    # cv2_utils.show_image(part, win_name='in_phone_menu')
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
    # cv2_utils.show_image(part, win_name='ELLIPSIS_PART')
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
    return im.match_template(part, 'ui_alert', threshold=0.7)


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

    ocr_map = ocr.match_words(part, words=['一键领取'], lcs_percent=0.55)
    if len(ocr_map) == 0:
        return None

    result: MatchResult = ocr_map.popitem()[1].max

    result.x += NAMELESS_HONOR_TAB_1_CLAIM_PART.x1
    result.y += NAMELESS_HONOR_TAB_1_CLAIM_PART.y1

    return result


def get_nameless_honor_tab_1_cancel_btn(screen: MatLike, ocr: OcrMatcher) -> Optional[MatchResult]:
    """
    获取无名勋礼第1个tab 【一键领取】后出现的取消按钮
    :param screen: 屏幕截图
    :param ocr: 文字识别器
    :return:
    """
    part, _ = cv2_utils.crop_image(screen, NAMELESS_HONOR_TAB_1_CANCEL_BTN)

    ocr_result = ocr.ocr_for_single_line(part)
    if str_utils.find_by_lcs(gt('取消', 'ocr'), ocr_result, percent=0.3):
        x, y = NAMELESS_HONOR_TAB_1_CANCEL_BTN.left_top.tuple()
        x2, y2 = NAMELESS_HONOR_TAB_1_CANCEL_BTN.left_top.tuple()
        w, h = x2 -x, y2 - y
        return MatchResult(1, x, y, w, h)

    return None


def get_training_activity_claim_btn_pos(screen: MatLike, ocr: OcrMatcher):
    """
    指南实训页面 获取活跃度【领取】按钮的位置 多个时随便返回一个
    :param screen:
    :param ocr:
    :return:
    """
    part, _ = cv2_utils.crop_image(screen, GUIDE_TRAINING_ACTIVITY_CLAIM_RECT)
    lower_color = np.array([0, 0, 0], dtype=np.uint8)  # 只取黑色部分 避免金色的【已领取】
    upper_color = np.array([30, 30, 30], dtype=np.uint8)
    black_part = cv2.inRange(part, lower_color, upper_color)
    # cv2_utils.show_image(black_part, 'get_nameless_honor_tab_pos')

    ocr_map = ocr.match_words(black_part, words=['领取'], lcs_percent=0.3)

    if len(ocr_map) == 0:
        return None

    result: MatchResult = ocr_map.popitem()[1].max

    result.x += GUIDE_TRAINING_ACTIVITY_CLAIM_RECT.x1
    result.y += GUIDE_TRAINING_ACTIVITY_CLAIM_RECT.y1

    return result


def get_training_reward_claim_btn_pos(screen: MatLike, im: ImageMatcher) -> Optional[MatchResult]:
    """
    指南实训页面 获取奖励领取按钮的位置 多个时返回最右边的一个
    :param screen:
    :param im:
    :return:
    """
    part, _ = cv2_utils.crop_image(screen, GUIDE_TRAINING_REWARD_CLAIM_RECT)

    result_list: MatchResultList = im.match_template(part, 'training_reward_gift', ignore_template_mask=True)

    if len(result_list) == 0:
        return None

    result: MatchResult = None
    for i in result_list:
        if result is None or i.x > result.x:
            result = i

    result.x += GUIDE_TRAINING_REWARD_CLAIM_RECT.x1
    result.y += GUIDE_TRAINING_REWARD_CLAIM_RECT.y1

    return result

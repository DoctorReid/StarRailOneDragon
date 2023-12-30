from cv2.typing import MatLike

from basic import Rect, str_utils, Point
from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.image.ocr_matcher import OcrMatcher

FINAL_ENTER_GAME_RECT = Rect(890, 1000, 1030, 1030)  # 无需密码 无需选区服的情况 【点击进入】
LOGIN_ENTER_GAME_RECT = Rect(900, 650, 1020, 680)  # 登录框的【进入游戏】
LOGIN_SWITCH_PASSWORD_RECT = Rect(0, 0, 0, 0)  # 登录框里的选择【账号密码】
LOGIN_ACCOUNT_RECT = Rect(0, 0, 0, 0)  # 登录框里的选择【输入手机号/邮箱】
LOGIN_PASSWORD_RECT = Rect(0, 0, 0, 0)  # 登录框里的选择【输入密码】
LOGIN_ACCEPT_POINT = Point(0, 0)  # 登录框里的选择【同意协议】
SERVER_ENTER_GAME_RECT = Rect(820, 810, 1110, 860)  # 选择区服时的【进入游戏】
EXPRESS_SUPPLY_RECT = Rect(870, 80, 1050, 130)  # 刚进入游戏时的领取月卡 【列车补给】


def in_final_enter_phase(screen: MatLike, ocr: OcrMatcher) -> bool:
    """
    当前界面在登录账号界面
    :param screen:
    :param ocr:
    :return:
    """
    part, _ = cv2_utils.crop_image(screen, FINAL_ENTER_GAME_RECT)

    ocr_result: str = ocr.ocr_for_single_line(part)

    if str_utils.find_by_lcs(gt('点击进入', 'ocr'), ocr_result, percent=0.55):
        return True

    return False


def in_login_phase(screen: MatLike, ocr: OcrMatcher) -> bool:
    """
    当前界面在登录界面
    :param screen:
    :param ocr:
    :return:
    """
    part, _ = cv2_utils.crop_image(screen, LOGIN_ENTER_GAME_RECT)

    ocr_result: str = ocr.ocr_for_single_line(part)

    if str_utils.find_by_lcs(gt('进入游戏', 'ocr'), ocr_result, percent=0.55):
        return True

    return False


def in_login_captcha_phase(screen: MatLike, ocr: OcrMatcher) -> bool:
    """
    当前界面在登录-输入验证码界面
    :param screen: 屏幕截图
    :param ocr:
    :return:
    """
    part, _ = cv2_utils.crop_image(screen, LOGIN_SWITCH_PASSWORD_RECT)
    return ocr.match_word_in_one_line(part, '账号密码', strict_one_line=True, lcs_percent=0.1)


def in_server_phase(screen: MatLike, ocr: OcrMatcher) -> bool:
    """
    当前界面在选择区服界面
    :param screen:
    :param ocr:
    :return:
    """
    part, _ = cv2_utils.crop_image(screen, SERVER_ENTER_GAME_RECT)

    ocr_result: str = ocr.ocr_for_single_line(part)

    if str_utils.find_by_lcs(gt('开始游戏', 'ocr'), ocr_result, percent=0.55):
        return True

    return False


def in_express_supply_phase(screen: MatLike, ocr: OcrMatcher) -> bool:
    """
    当前界面在领取小月卡奖励界面
    :param screen:
    :param ocr:
    :return:
    """
    part, _ = cv2_utils.crop_image(screen, EXPRESS_SUPPLY_RECT)

    ocr_result: str = ocr.ocr_for_single_line(part)

    if str_utils.find_by_lcs(gt('列车补给', 'ocr'), ocr_result, percent=0.55):
        return True

    return False
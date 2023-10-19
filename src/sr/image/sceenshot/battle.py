import cv2
import numpy as np
from cv2.typing import MatLike

from basic.img import MatchResult, cv2_utils
from sr.image import ImageMatcher

UNKNOWN = 0
IN_WORLD = 1
ENTERING_BATTLE = 2
BATTLING = 3
ENDING_BATTLE_SUCCESS = 4
ENDING_BATTLE_FAIL = 5

CTRL_RECT = (1620, 30, 1900, 70)
FAST_BATTLE_RECT = (1620, 30, 1700, 70)  # 二倍速
AUTO_BATTLE_RECT = (1700, 30, 1800, 70)  # 自动战斗
PAUSE_BATTLE_RECT = (1800, 30, 1900, 70)  # 暂停


def get_battle_status(screen: MatLike, im: ImageMatcher):
    """
    判断当天屏幕的战斗状态
    :param screen: 屏幕截图
    :param im: 图片匹配器
    :return: 状态
    """
    if is_character_icon_at_right_top(screen, im):
        return IN_WORLD
    if match_battle_ctrl(screen, im, 'battle_ctrl_01') is not None:
        return BATTLING

    return UNKNOWN


def is_character_icon_at_right_top(screen: MatLike, im: ImageMatcher):
    """
    右上角是否有角色的图标
    :param screen: 屏幕截图
    :param im: 图片匹配器
    :return: 右上角是否有角色的图标
    """
    part = screen[0:90, 1800:1900]
    result = im.match_template(part, 'ui_icon_01', threshold=0.7)
    return result.max is not None


def is_auto_battle_on(screen: MatLike, im: ImageMatcher):
    """
    通过右上角自动战斗图标是否点亮 判断是否开启了自动战斗
    :param screen: 屏幕截图
    :param im: 图片匹配器
    :return: 是否已经开启了自动战斗
    """
    return match_battle_ctrl(screen, im, 'battle_ctrl_02', rect=AUTO_BATTLE_RECT) is not None


def is_fast_battle_on(screen: MatLike, im: ImageMatcher):
    """
    通过右上角二倍速图标是否点亮 判断是否开启了二倍速
    :param screen: 屏幕截图
    :param im: 图片匹配器
    :return: 是否已经开启了二倍速
    """
    return match_battle_ctrl(screen, im, 'battle_ctrl_03', rect=FAST_BATTLE_RECT) is not None or \
        match_battle_ctrl(screen, im, 'battle_ctrl_04', rect=FAST_BATTLE_RECT) is not None


def match_battle_ctrl(screen: MatLike, im: ImageMatcher, template_id: str, rect = CTRL_RECT) -> MatchResult:
    """
    匹配战斗控制按钮所在位置
    :param screen: 屏幕截图
    :param im: 图片匹配器
    :param template_id: 模板id
    :param rect: 图标应该所在的位置
    :return:
    """
    part, _ = cv2_utils.crop_image(screen, rect)
    cv2_utils.show_image(part, wait=0)
    b, g, r = cv2.split(part)

    # 找到亮的部分
    mask = np.zeros((part.shape[0], part.shape[1]), dtype=np.uint8)
    lower = 170
    mask[np.where(b > lower)] = 255
    mask[np.where(g > lower)] = 255
    mask[np.where(r > lower)] = 255

    mr = im.match_template(mask, template_id, template_type='mask', threshold=0.4, ignore_template_mask=True)
    r = mr.max

    if r is not None:
        r.x += 1620
        r.y += 30

    return r

from typing import Optional

import cv2
import numpy as np
from cv2.typing import MatLike

from basic import Rect, Point, str_utils
from basic.i18_utils import gt
from basic.img import MatchResult, cv2_utils
from sr.image import ImageMatcher
from sr.image.ocr_matcher import OcrMatcher

UNKNOWN = 0
IN_WORLD = 1
ENTERING_BATTLE = 2
BATTLING = 3
ENDING_BATTLE_SUCCESS = 4
ENDING_BATTLE_FAIL = 5

CTRL_RECT = Rect(1620, 30, 1900, 70)
FAST_BATTLE_RECT = Rect(1620, 30, 1700, 70)  # 二倍速
AUTO_BATTLE_RECT = Rect(1700, 30, 1800, 70)  # 自动战斗
PAUSE_BATTLE_RECT = Rect(1800, 30, 1900, 70)  # 暂停

# 右上方那一行的菜单
RT_CHARACTER_RECT = Rect(1800, 0, 1900, 90)  # 角色按钮

AFTER_BATTLE_RESULT_RECT_1 = Rect(820, 240, 1100, 320)  # 战斗结束后领奖励页面 上方的结果框 有奖励的时候
AFTER_BATTLE_RESULT_RECT_2 = Rect(790, 235, 1150, 305)  # 战斗结束后领奖励页面 上方的结果框 无奖励的时候

AFTER_BATTLE_CHALLENGE_AGAIN_BTN_RECT = Rect(1180, 930, 1330, 960)  # 战斗结束后领奖励页面 【再来一次】按钮
AFTER_BATTLE_EXIT_BTN_RECT = Rect(640, 930, 780, 960)  # 战斗结束后领奖励页面 【退出关卡】按钮


def get_battle_status(screen: MatLike, im: ImageMatcher):
    """
    判断当天屏幕的战斗状态
    :param screen: 屏幕截图
    :param im: 图片匹配器
    :return: 状态
    """
    if is_character_icon_at_right_top(screen, im):
        return IN_WORLD
    if match_battle_ctrl(screen, im, 'battle_ctrl_01', rect=PAUSE_BATTLE_RECT) is not None:
        return BATTLING

    return UNKNOWN


def is_character_icon_at_right_top(screen: MatLike, im: ImageMatcher):
    """
    右上角是否有角色的图标
    :param screen: 屏幕截图
    :param im: 图片匹配器
    :return: 右上角是否有角色的图标
    """
    part, _ = cv2_utils.crop_image(screen, RT_CHARACTER_RECT)
    result = im.match_template(part, 'ui_icon_01', threshold=0.7)
    return result.max is not None


def is_auto_battle_on(screen: MatLike, im: ImageMatcher):
    """
    通过右上角自动战斗图标是否点亮 判断是否开启了自动战斗
    1. 直接看是否已经存在自动战斗激活的图标 存在则返回 True
    2. 如果1不存在 看是否存在暂停按键 不存在则返回 True 部分动画过程三个按键都会消失
    :param screen: 屏幕截图
    :param im: 图片匹配器
    :return: 是否已经开启了自动战斗 部分情况画面没加载完毕 认为已经默认开启
    """
    on: bool = match_battle_ctrl(screen, im, 'battle_ctrl_02', rect=AUTO_BATTLE_RECT) is not None
    if on:
        return True
    no_pause: bool = match_battle_ctrl(screen, im, 'battle_ctrl_01', rect=PAUSE_BATTLE_RECT, threshold=0.5) is None
    if no_pause:  # 暂停键都看不到 说明在某个动画过程
        return True
    return False


def is_fast_battle_on(screen: MatLike, im: ImageMatcher):
    """
    通过右上角二倍速图标是否点亮 判断是否开启了二倍速
    1. 直接看是否已经存在快速战斗的图标 存在则返回 True
    2. 如果1不存在 看是否存在禁止改变二倍速的图标 存在则返回 True 部分动画过程禁止改变二倍速
    3. 如果2不存在 看是否存在暂停按键 不存在则返回 True 部分动画过程三个按键都会消失
    :param screen: 屏幕截图
    :param im: 图片匹配器
    :return: 是否已经开启了二倍速
    """
    on: bool = match_battle_ctrl(screen, im, 'battle_ctrl_03', rect=FAST_BATTLE_RECT) is not None
    if on:
        return True
    cant_fast: bool = match_battle_ctrl(screen, im, 'battle_ctrl_04', rect=FAST_BATTLE_RECT, lower_color=130) is not None
    if cant_fast:  # 部分动画过程禁止改变二倍速
        return True
    no_pause: bool = match_battle_ctrl(screen, im, 'battle_ctrl_01', rect=PAUSE_BATTLE_RECT, threshold=0.5) is None
    if no_pause:  # 暂停键都看不到 说明在某个动画过程
        return True
    return False


def match_battle_ctrl(screen: MatLike, im: ImageMatcher, template_id: str, rect: Rect = CTRL_RECT,
                      is_on: bool = True, lower_color: int = None, threshold: float = 0.4) -> MatchResult:
    """
    匹配战斗控制按钮所在位置
    :param screen: 屏幕截图
    :param im: 图片匹配器
    :param template_id: 模板id
    :param rect: 图标应该所在的位置
    :param is_on: 是否激活
    :param lower_color: 特殊情况下自定义使用的颜色阈值 目前仅自动战斗使用
    :param threshold: 自定义匹配阈值 暂停键比较简单 阈值要高一点
    :return:
    """
    part, _ = cv2_utils.crop_image(screen, rect)
    b, g, r = cv2.split(part)

    # 找到亮的部分
    mask = np.zeros((part.shape[0], part.shape[1]), dtype=np.uint8)
    lower = 230 if is_on else 100
    if lower_color is not None:
        lower = lower_color
    mask[np.where(b > lower)] = 255
    mask[np.where(g > lower)] = 255
    mask[np.where(r > lower)] = 255

    mr = im.match_template(mask, template_id, template_type='mask', threshold=threshold, ignore_template_mask=True)
    r = mr.max

    # cv2_utils.show_image(mask, r, wait=0)

    if r is not None:
        r.x += 1620
        r.y += 30

    return r


def get_battle_result_str(screen: MatLike, ocr: OcrMatcher) -> Optional[str]:
    """
    战斗结束时，领取奖励的页面
    获取顶部挑战结果
    :param screen:
    :param ocr:
    :return: "挑战成功" 或 "挑战失败"
    """
    for rect in [AFTER_BATTLE_RESULT_RECT_1, AFTER_BATTLE_RESULT_RECT_2]:
        part, _ = cv2_utils.crop_image(screen, rect)
        ocr_result = ocr.ocr_for_single_line(part, strict_one_line=True)
        if str_utils.find_by_lcs(gt('成功', 'ocr'), ocr_result, percent=0.1):
            return gt('挑战成功', 'ocr')
        elif str_utils.find_by_lcs(gt('失败', 'ocr'), ocr_result, percent=0.1):
            return gt('挑战失败', 'ocr')

    return None

from cv2.typing import MatLike

from basic.i18_utils import gt
from sr.image import OcrMatcher, ImageMatcher

IN_WORLD = 1
ENTERING_BATTLE = 2
BATTLING = 3
ENDING_BATTLE_SUCCESS = 4
ENDING_BATTLE_FAIL = 5


def get_battle_status(screen: MatLike, im: ImageMatcher):
    """
    判断当天屏幕的战斗状态
    :param screen: 屏幕截图
    :param im: 图片匹配器
    :return: 状态
    """
    if is_character_icon_at_right_top(screen, im):
        return IN_WORLD


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
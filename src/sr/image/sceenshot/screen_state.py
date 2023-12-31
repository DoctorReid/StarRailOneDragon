from enum import Enum

from cv2.typing import MatLike, Rect

from basic.img import cv2_utils
from sr.image import ImageMatcher
from sr.image.ocr_matcher import OcrMatcher
from sr.image.sceenshot import secondary_ui
from sr.image.sceenshot.phone_menu import in_phone_menu


class ScreenState(Enum):

    # 大世界部分
    NORMAL_IN_WORLD: int = 100
    """大世界主界面 右上角有角色的图标"""

    PHONE_MENU: int = 101
    """菜单 有显示开拓等级"""

    # 二级页面 - 指南
    GUIDE_OPERATION_BRIEFING: int = 200
    """行动摘要"""

    GUIDE_DAILY_TRAINING: int = 201
    """每日实训"""

    GUIDE_SURVIVAL_INDEX: int = 202
    """生存索引"""

    GUIDE_TREASURES_LIGHTWARD: int = 203
    """逐光捡金"""

    GUIDE_STRATEGIC_TRAINING: int = 204
    """战术训练"""


def get_screen_state(screen: MatLike, im: ImageMatcher, ocr: OcrMatcher) -> ScreenState:
    if is_normal_in_world(screen, im):
        return ScreenState.NORMAL_IN_WORLD
    if in_phone_menu(screen, ocr):
        return ScreenState.PHONE_MENU
    if secondary_ui.in_secondary_ui(screen, ocr, secondary_ui.SecondaryUiTitle.TITLE_GUIDE.value, lcs_percent=0.1):
        pass


def is_normal_in_world(screen: MatLike, im: ImageMatcher) -> bool:
    """
    是否在普通大世界主界面 - 右上角是否有角色的图标
    :param screen: 屏幕截图
    :param im: 图片匹配器
    :return:
    """
    part, _ = cv2_utils.crop_image(screen, Rect(1800, 0, 1900, 90))
    result = im.match_template(part, 'ui_icon_01', threshold=0.7)
    return result.max is not None

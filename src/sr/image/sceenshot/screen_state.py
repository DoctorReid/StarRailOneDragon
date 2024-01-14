from enum import Enum

from cv2.typing import MatLike

from basic import Rect, str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.image import ImageMatcher
from sr.image.ocr_matcher import OcrMatcher
from sr.image.sceenshot.phone_menu import in_phone_menu


class ScreenState(Enum):

    # 大世界部分
    NORMAL_IN_WORLD: str = '大世界'
    """大世界主界面 右上角有角色的图标"""

    PHONE_MENU: str = '菜单'
    """菜单 有显示开拓等级"""

    # 二级页面 - 指南
    GUIDE: str = '星际和平指南'
    """星际和平指南"""

    GUIDE_OPERATION_BRIEFING: str = '行动摘要'
    """星际和平指南 - 行动摘要"""

    GUIDE_DAILY_TRAINING: str = '每日实训'
    """星际和平指南 - 每日实训"""

    GUIDE_SURVIVAL_INDEX: str = '生存索引'
    """星际和平指南 - 生存索引"""

    GUIDE_TREASURES_LIGHTWARD: str = '逐光捡金'
    """星际和平指南 - 逐光捡金"""

    GUIDE_STRATEGIC_TRAINING: str = '战术训练'
    """星际和平指南 - 战术训练"""

    FORGOTTEN_HALL: str = '忘却之庭'
    """忘却之庭"""

    MEMORY_OF_CHAOS: str = '混沌回忆'
    """忘却之庭 - 混沌回忆"""

    PURE_FICTION: str = '虚构叙事'
    """虚构叙事"""

    NAMELESS_HONOR: str = '无名勋礼'
    """无名勋礼"""

    NH_REWARDS: str = '奖励'
    """无名勋礼 - 奖励"""

    NH_MISSIONS: str = '任务'
    """无名勋礼 - 任务"""

    NH_TREASURE: str = '星海宝藏'
    """无名勋礼 - 星海宝藏"""

    INVENTORY: str = '背包'
    """背包"""

    SYNTHESIZE: str = '合成'
    """合成"""

    TEAM: str = '队伍'
    """队伍"""

    SIM_TYPE_NORMAL: str = '模拟宇宙'
    """模拟宇宙 - 普通"""

    SIM_TYPE_EXTEND: str = '扩展装置'
    """模拟宇宙 - 拓展装置"""

    SIM_PATH: str = '命途'
    """模拟宇宙 - 命途"""

    SIM_BLESS: str = '选择祝福'
    """模拟宇宙 - 选择祝福"""

    SIM_CURIOS: str = '选择奇物'
    """模拟宇宙 - 选择奇物"""

    SIM_EVENT: str = '事件'
    """模拟宇宙 - 事件"""

    BATTLE: str = '战斗'
    """所有战斗画面通用 - 右上角有暂停符号"""


class TargetRect(Enum):

    UI_TITLE = Rect(98, 39, 350, 100)
    """左上角界面名称的位置"""

    CHARACTER_ICON = Rect(1800, 0, 1900, 90)
    """右上角角色图标的位置"""

    REGION_NAME = Rect(52, 13, 276, 40)
    """左上角区域名字的位置"""

    SIM_UNI_UI_TITLE = Rect(100, 15, 350, 100)
    """模拟宇宙 - 左上角界面名称的位置"""

    EMPTY_TO_CONTINUE = Rect(775, 836, 1166, 1066)
    """点击空白处关闭"""

def get_screen_state(screen: MatLike, im: ImageMatcher, ocr: OcrMatcher) -> ScreenState:
    if is_normal_in_world(screen, im):
        return ScreenState.NORMAL_IN_WORLD
    if in_phone_menu(screen, ocr):
        return ScreenState.PHONE_MENU
    if in_secondary_ui(screen, ocr, ScreenState.GUIDE.value, lcs_percent=0.1):
        pass


def is_normal_in_world(screen: MatLike, im: ImageMatcher) -> bool:
    """
    是否在普通大世界主界面 - 右上角是否有角色的图标
    :param screen: 屏幕截图
    :param im: 图片匹配器
    :return:
    """
    part, _ = cv2_utils.crop_image(screen, TargetRect.CHARACTER_ICON.value)
    result = im.match_template(part, 'ui_icon_01', threshold=0.7)
    return result.max is not None


def in_secondary_ui(screen: MatLike, ocr: OcrMatcher,
                    title_cn: str, lcs_percent: float = 0.3,
                    rect: Rect = TargetRect.UI_TITLE.value) -> bool:
    """
    根据页面左上方标题文字 判断在哪个二级页面中
    :param screen: 屏幕截图
    :param ocr: OCR识别
    :param title_cn: 中文标题
    :param lcs_percent: LCS阈值
    :param rect: 区域
    :return:
    """
    part, _ = cv2_utils.crop_image(screen, rect)
    # cv2_utils.show_image(part, wait=0)
    ocr_map = ocr.match_words(part, words=[gt(title_cn, 'ui')],
                              lcs_percent=lcs_percent, merge_line_distance=10)

    return len(ocr_map) > 0


def in_sim_uni_secondary_ui(screen: MatLike, ocr: OcrMatcher) -> bool:
    """
    判断是否在模拟宇宙的页面
    :param screen: 页面截图
    :param ocr: OCR
    :return:
    """
    return in_secondary_ui(screen, ocr, ScreenState.SIM_TYPE_NORMAL.value,
                           rect=TargetRect.SIM_UNI_UI_TITLE.value)


def in_sim_uni_choose_bless(screen: MatLike, ocr: OcrMatcher) -> bool:
    """
    是否在模拟宇宙-选择祝福页面
    :param screen: 页面截图
    :param ocr: OCR
    :return:
    """
    return in_secondary_ui(screen, ocr, ScreenState.SIM_BLESS.value, lcs_percent=0.55)


def in_sim_uni_choose_curio(screen: MatLike, ocr: OcrMatcher) -> bool:
    """
    是否在模拟宇宙-选择奇物页面
    :param screen: 页面截图
    :param ocr: OCR
    :return:
    """
    return in_secondary_ui(screen, ocr, ScreenState.SIM_CURIOS.value, lcs_percent=0.55)


def in_sim_uni_event(screen: MatLike, ocr: OcrMatcher) -> bool:
    """
    是否在模拟宇宙-事件页面
    :param screen: 页面截图
    :param ocr: OCR
    :return:
    """
    return in_secondary_ui(screen, ocr, ScreenState.SIM_EVENT.value)


def get_region_name(screen: MatLike, ocr: OcrMatcher) -> str:
    """
    获取当前屏幕 左上角显示的区域名字
    需要确保是在大世界界面
    :param screen: 页面截图
    :param ocr: OCR
    :return:
    """
    part, _ = cv2_utils.crop_image(screen, TargetRect.REGION_NAME.value)
    return ocr.ocr_for_single_line(part)


def is_empty_to_close(screen: MatLike, ocr: OcrMatcher) -> bool:
    """
    是否点击空白处关闭
    :param screen:
    :param ocr:
    :return:
    """
    part, _ = cv2_utils.crop_image(screen, TargetRect.EMPTY_TO_CONTINUE.value)
    ocr_result = ocr.ocr_for_single_line(part)
    # cv2_utils.show_image(part, wait=0)

    return str_utils.find_by_lcs(gt('点击空白处关闭', 'ui'), ocr_result)
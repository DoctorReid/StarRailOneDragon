from enum import Enum
from typing import List, Optional

from cv2.typing import MatLike

from basic import Rect, str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.image import ImageMatcher
from sr.image.ocr_matcher import OcrMatcher
from sr.image.sceenshot.phone_menu import in_phone_menu
from sr.screen_area import ScreenArea
from sr.screen_area.dialog import ScreenDialog
from sr.sim_uni.sim_uni_const import SimUniLevelTypeEnum


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

    SIM_TYPE_GOLD: str = '黄金与机械'
    """模拟宇宙 - 黄金与机械"""

    SIM_PATH: str = '命途'
    """模拟宇宙 - 命途"""

    SIM_BLESS: str = '选择祝福'
    """模拟宇宙 - 选择祝福"""

    SIM_DROP_BLESS: str = '丢弃祝福'
    """模拟宇宙 - 丢弃祝福"""

    SIM_UPGRADE_BLESS: str = '祝福强化'
    """模拟宇宙 - 祝福强化"""

    SIM_CURIOS: str = '选择奇物'
    """模拟宇宙 - 选择奇物"""

    SIM_DROP_CURIOS: str = '丢弃奇物'
    """模拟宇宙 - 丢弃奇物"""

    SIM_EVENT: str = '事件'
    """模拟宇宙 - 事件"""

    SIM_REWARD: str = '沉浸奖励'
    """模拟宇宙 - 沉浸奖励"""

    SIM_UNI_REGION: str = '模拟宇宙-区域'
    """模拟宇宙 - 区域"""

    BATTLE: str = '战斗'
    """所有战斗画面通用 - 右上角有暂停符号"""

    BATTLE_FAIL: str = '战斗失败'
    """所有战斗画面通用 - 右上角有暂停符号"""

    EMPTY_TO_CLOSE: str = '点击空白处关闭'
    """所有画面通用 - 下方有 点击空白处关闭"""

    TP_BATTLE_SUCCESS: str = '挑战成功'
    """开拓力副本 - 挑战成功"""

    TP_BATTLE_FAIL: str = '战斗失败'
    """开拓力副本 - 战斗失败"""


class TargetRect(Enum):

    UI_TITLE = Rect(98, 39, 350, 100)
    """左上角界面名称的位置"""

    CHARACTER_ICON = Rect(1800, 0, 1900, 90)
    """右上角角色图标的位置"""

    REGION_NAME = Rect(52, 13, 276, 40)
    """左上角区域名字的位置"""

    SIM_UNI_UI_TITLE = Rect(100, 15, 350, 100)
    """模拟宇宙 - 左上角界面名称的位置 事件和选择祝福的框是不一样位置的 这里取了两者的并集"""

    SIM_UNI_REWARD = Rect(760, 343, 1200, 382)
    """模拟宇宙 - 中间的位置 沉浸奖励"""

    BATTLE_FAIL = Rect(783, 231, 1141, 308)
    """战斗失败"""

    AFTER_BATTLE_RESULT_RECT_1 = Rect(820, 240, 1100, 320)
    """战斗结束后领奖励页面 上方的结果框 有奖励的时候"""
    AFTER_BATTLE_RESULT_RECT_2 = Rect(820, 205, 1100, 278)
    """战斗结束后领奖励页面 上方的结果框 有双倍奖励的时候"""
    AFTER_BATTLE_RESULT_RECT_3 = Rect(820, 320, 1100, 380)
    """战斗结束后领奖励页面 上方的结果框 无奖励的时候"""

    EMPTY_TO_CLOSE = Rect(876, 878, 1048, 1026)
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


def get_ui_title(screen: MatLike, ocr: OcrMatcher,
                 rect: Rect = TargetRect.UI_TITLE.value) -> List[str]:
    """
    获取页面左上方标题文字 可能有两个
    例如 模拟宇宙 选择祝福
    :param screen: 屏幕截图
    :param ocr: OCR识别
    :param rect: 区域
    :return:
    """
    part = cv2_utils.crop_image_only(screen, rect)
    # cv2_utils.show_image(part, wait=0)
    ocr_result_map = ocr.run_ocr(part)
    return list(ocr_result_map.keys())


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


def in_sim_uni_choose_path(screen: MatLike, ocr: OcrMatcher) -> bool:
    """
    是否在模拟宇宙-选择命途页面
    :param screen: 页面截图
    :param ocr: OCR
    :return:
    """
    return in_secondary_ui(screen, ocr, ScreenState.SIM_PATH.value, lcs_percent=0.1,
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
    part = cv2_utils.crop_image_only(screen, TargetRect.EMPTY_TO_CLOSE.value)
    ocr_result = ocr.match_one_best_word(part, '点击空白处关闭', lcs_percent=0.1)
    # cv2_utils.show_image(part, wait=0)

    return ocr_result is not None


def is_battle_fail(screen: MatLike, ocr: OcrMatcher) -> bool:
    """
    是否战斗失败
    :param screen: 屏幕截图
    :param ocr: OCR
    :return:
    """
    part, _ = cv2_utils.crop_image(screen, TargetRect.BATTLE_FAIL.value)
    ocr_result = ocr.ocr_for_single_line(part)

    return str_utils.find_by_lcs(gt('战斗失败', 'ui'), ocr_result, percent=0.51)


def is_sim_uni_get_reward(screen: MatLike, ocr: OcrMatcher) -> bool:
    """
    是否在模拟宇宙-沉浸奖励画面
    :param screen: 屏幕截图
    :param ocr: OCR
    :return:
    """
    part = cv2_utils.crop_image_only(screen, TargetRect.SIM_UNI_REWARD.value)
    ocr_result = ocr.ocr_for_single_line(part)
    return str_utils.find_by_lcs(gt('沉浸奖励', 'ocr'), ocr_result, percent=0.1)


def in_screen_by_area_text(screen: MatLike, ocr: OcrMatcher, area: ScreenArea) -> bool:
    """
    是否在一个目标画面 通过一个区域文本判断
    :param screen:
    :param ocr:
    :param area:
    :return:
    """
    part = cv2_utils.crop_image_only(screen, area.rect)
    ocr_result = ocr.ocr_for_single_line(part)
    return str_utils.find_by_lcs(gt(area.text, 'ocr'), ocr_result, percent=area.lcs_percent)


def get_sim_uni_screen_state(
        screen: MatLike, im: ImageMatcher, ocr: OcrMatcher,
        in_world: bool = False,
        empty_to_close: bool = False,
        bless: bool = False,
        drop_bless: bool = False,
        upgrade_bless: bool = False,
        curio: bool = False,
        drop_curio: bool = False,
        event: bool = False,
        battle: bool = False,
        battle_fail: bool = False,
        reward: bool = False,
        fast_recover: bool = False) -> Optional[str]:
    """
    获取模拟宇宙中的画面状态
    :param screen: 屏幕截图
    :param im: 图片匹配器
    :param ocr: 文本识别器
    :param in_world: 可能在大世界
    :param empty_to_close: 可能点击空白处关闭
    :param bless: 可能在选择祝福
    :param drop_bless: 可能在丢弃祝福
    :param upgrade_bless: 可能在祝福强化
    :param curio: 可能在选择奇物
    :param drop_curio: 可能在丢弃奇物
    :param event: 可能在事件
    :param battle: 可能在战斗
    :param battle_fail: 可能在战斗失败
    :param reward: 可能在沉浸奖励
    :param fast_recover: 可能在快速恢复
    :return:
    """
    if in_world and is_normal_in_world(screen, im):
        return ScreenState.NORMAL_IN_WORLD.value

    if battle_fail and is_battle_fail(screen, ocr):
        return ScreenState.BATTLE_FAIL.value

    if empty_to_close and is_empty_to_close(screen, ocr):
        return ScreenState.EMPTY_TO_CLOSE.value

    if reward and is_sim_uni_get_reward(screen, ocr):
        return ScreenState.SIM_REWARD.value

    if fast_recover and in_screen_by_area_text(screen, ocr, ScreenDialog.FAST_RECOVER_TITLE.value):
        return ScreenDialog.FAST_RECOVER_TITLE.value.text

    titles = get_ui_title(screen, ocr, rect=TargetRect.SIM_UNI_UI_TITLE.value)
    sim_uni_idx = str_utils.find_best_match_by_lcs(ScreenState.SIM_TYPE_NORMAL.value, titles)
    gold_idx = str_utils.find_best_match_by_lcs(ScreenState.SIM_TYPE_GOLD.value, titles)  # 不知道是不是游戏bug 游戏内正常的模拟宇宙也会显示这个

    if sim_uni_idx is None and gold_idx is None:
        if battle:  # 有判断的时候 不在前面的情况 就认为是战斗
            return ScreenState.BATTLE.value
        return None

    if bless and str_utils.find_best_match_by_lcs(ScreenState.SIM_BLESS.value, titles, lcs_percent_threshold=0.51) is not None:
        return ScreenState.SIM_BLESS.value

    if drop_bless and str_utils.find_best_match_by_lcs(ScreenState.SIM_DROP_BLESS.value, titles, lcs_percent_threshold=0.51) is not None:
        return ScreenState.SIM_DROP_BLESS.value

    if upgrade_bless and str_utils.find_best_match_by_lcs(ScreenState.SIM_UPGRADE_BLESS.value, titles, lcs_percent_threshold=0.51) is not None:
        return ScreenState.SIM_UPGRADE_BLESS.value

    if curio and str_utils.find_best_match_by_lcs(ScreenState.SIM_CURIOS.value, titles, lcs_percent_threshold=0.51):
        return ScreenState.SIM_CURIOS.value

    if drop_curio and str_utils.find_best_match_by_lcs(ScreenState.SIM_DROP_CURIOS.value, titles, lcs_percent_threshold=0.51):
        return ScreenState.SIM_DROP_CURIOS.value

    if event and str_utils.find_best_match_by_lcs(ScreenState.SIM_EVENT.value, titles):
        return ScreenState.SIM_EVENT.value

    if battle:  # 有判断的时候 不在前面的情况 就认为是战斗
        return ScreenState.BATTLE.value

    return None


def get_sim_uni_initial_screen_state(screen: MatLike, im: ImageMatcher, ocr: OcrMatcher) -> Optional[str]:
    """
    获取模拟宇宙应用开始时的画面
    :param screen: 屏幕截图
    :param im: 图片匹配器
    :param ocr: 文本识别器
    :return:
    """
    if is_normal_in_world(screen, im):
        region_name = get_region_name(screen, ocr)
        for level_type_enum in SimUniLevelTypeEnum:
            if str_utils.find_by_lcs(gt(level_type_enum.value.type_name, 'ocr'), region_name, percent=0.51):
                return ScreenState.SIM_UNI_REGION.value

        return ScreenState.NORMAL_IN_WORLD.value

    if in_phone_menu(screen, ocr):
        return ScreenState.PHONE_MENU.value

    titles = get_ui_title(screen, ocr, rect=TargetRect.UI_TITLE.value)

    if str_utils.find_best_match_by_lcs(ScreenState.GUIDE.value, titles, lcs_percent_threshold=0.5) is not None:
        if str_utils.find_best_match_by_lcs(ScreenState.GUIDE_SURVIVAL_INDEX.value, titles, lcs_percent_threshold=0.5) is not None:
            return ScreenState.GUIDE_SURVIVAL_INDEX.value

        return ScreenState.GUIDE.value

    if str_utils.find_best_match_by_lcs(ScreenState.SIM_TYPE_EXTEND.value, titles, lcs_percent_threshold=0.5) is not None:
        return ScreenState.SIM_TYPE_EXTEND.value

    if str_utils.find_best_match_by_lcs(ScreenState.SIM_TYPE_NORMAL.value, titles, lcs_percent_threshold=0.5) is not None:
        return ScreenState.SIM_TYPE_NORMAL.value

    return None


def get_world_patrol_screen_state(
        screen: MatLike, im: ImageMatcher, ocr: OcrMatcher,
        in_world: bool = False,
        battle: bool = False,
        battle_fail: bool = False,
        fast_recover: bool = False):
    """
    获取锄大地的画面状态
    :param screen: 屏幕截图
    :param im: 图片匹配器
    :param ocr: 文本识别器
    :param in_world: 可能在大世界
    :param battle: 可能在战斗
    :param battle_fail: 可能在战斗失败
    :param fast_recover: 可能在快速恢复
    :return:
    """
    if in_world and is_normal_in_world(screen, im):
        return ScreenState.NORMAL_IN_WORLD.value

    if battle_fail and is_battle_fail(screen, ocr):
        return ScreenState.BATTLE_FAIL.value

    if fast_recover and in_screen_by_area_text(screen, ocr, ScreenDialog.FAST_RECOVER_TITLE.value):
        return ScreenDialog.FAST_RECOVER_TITLE.value.text

    if battle:  # 有判断的时候 不在前面的情况 就认为是战斗
        return ScreenState.BATTLE.value

    return None


def get_tp_battle_screen_state(
        screen: MatLike, im: ImageMatcher, ocr: OcrMatcher,
        in_world: bool = False,
        battle_success: bool = False,
        battle_fail: bool = False) -> str:
    """
    获取开拓力副本战斗的画面状态
    :param screen: 屏幕截图
    :param im: 图片匹配器
    :param ocr: 文本识别器
    :param in_world: 可能在大世界
    :param battle_success: 可能在战斗
    :param battle_fail: 可能在战斗失败
    :return:
    """
    if in_world and is_normal_in_world(screen, im):
        return ScreenState.NORMAL_IN_WORLD.value

    for rect in [
        TargetRect.AFTER_BATTLE_RESULT_RECT_1.value,
        TargetRect.AFTER_BATTLE_RESULT_RECT_2.value,
        TargetRect.AFTER_BATTLE_RESULT_RECT_3.value,
    ]:
        part, _ = cv2_utils.crop_image(screen, rect)
        ocr_result = ocr.ocr_for_single_line(part, strict_one_line=True)
        if battle_success and str_utils.find_by_lcs(gt('挑战成功', 'ocr'), ocr_result, percent=0.51):
            return ScreenState.TP_BATTLE_SUCCESS.value
        elif battle_fail and str_utils.find_by_lcs(gt('战斗失败', 'ocr'), ocr_result, percent=0.51):
            return ScreenState.TP_BATTLE_FAIL.value

    return ScreenState.BATTLE.value

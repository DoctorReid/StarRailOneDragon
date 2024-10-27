from cv2.typing import MatLike
from enum import Enum
from typing import Optional, List

from one_dragon.base.screen import screen_utils
from one_dragon.base.screen.screen_utils import FindAreaResultEnum
from one_dragon.utils import cv2_utils, str_utils
from one_dragon.utils.i18_utils import gt
from sr_od.app.sim_uni.sim_uni_const import SimUniLevelType, SimUniLevelTypeEnum
from sr_od.context.sr_context import SrContext
from sr_od.screen_state import common_screen_state, fast_recover_screen_state, battle_screen_state


class ScreenState(Enum):

    NORMAL_IN_WORLD: str = '大世界'
    EMPTY_TO_CLOSE: str = '点击空白处关闭'
    SIM_REWARD: str = '沉浸奖励'
    SIM_TYPE_NORMAL: str = '模拟宇宙'  # 模拟宇宙 - 普通
    SIM_TYPE_EXTEND: str = '扩展装置'  # 模拟宇宙 - 拓展装置
    SIM_TYPE_GOLD: str = '黄金与机械'  # 模拟宇宙 - 黄金与机械
    SIM_BLESS: str = '选择祝福'
    SIM_DROP_BLESS: str = '丢弃祝福'
    SIM_UPGRADE_BLESS: str = '祝福强化'
    SIM_CURIOS: str = '选择奇物'
    SIM_DROP_CURIOS: str = '丢弃奇物'
    SIM_EVENT: str = '事件'
    SIM_UNI_REGION: str = '模拟宇宙-区域'


def get_level_type(ctx: SrContext, screen: MatLike) -> Optional[SimUniLevelType]:
    """
    获取当前画面的楼层类型
    :param ctx: 上下文
    :param screen: 游戏画面
    :return:
    """
    area = ctx.screen_loader.get_area('模拟宇宙', '楼层类型')
    part = cv2_utils.crop_image_only(screen, area.rect)
    region_name = ctx.ocr.run_ocr_single_line(part)
    level_type_list: List[SimUniLevelType] = [enum.value for enum in SimUniLevelTypeEnum]
    target_list = [gt(level_type.type_name, 'ocr') for level_type in level_type_list]
    target_idx = str_utils.find_best_match_by_lcs(region_name, target_list, lcs_percent_threshold=0.61)

    if target_idx is None:
        return None
    else:
        return level_type_list[target_idx]


def get_sim_uni_screen_state(
        ctx: SrContext, screen: MatLike,
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
        fast_recover: bool = False,
        express_supply: bool = False,
        sim_uni: bool = False
) -> Optional[str]:
    """
    获取模拟宇宙中的画面状态
    :param ctx: 上下文
    :param screen: 游戏画面
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
    :param express_supply: 可能在列车补给
    :param sim_uni: 2.3版本新增 宇宙开始时选择祝福显示的是 模拟宇宙
    :return:
    """
    if in_world and common_screen_state.is_normal_in_world(ctx, screen):
        return ScreenState.NORMAL_IN_WORLD.value

    if battle_fail and battle_screen_state.is_battle_fail(ctx, screen):
        return battle_screen_state.ScreenState.BATTLE_FAIL.value

    if empty_to_close and is_empty_to_close(ctx, screen):
        return ScreenState.EMPTY_TO_CLOSE.value

    if reward and is_sim_uni_get_reward(ctx, screen):
        return ScreenState.SIM_REWARD.value

    if fast_recover and fast_recover_screen_state.is_fast_recover(ctx, screen):
        return fast_recover_screen_state.ScreenState.FAST_RECOVER.value

    if express_supply and common_screen_state.is_express_supply(ctx, screen):
        return common_screen_state.ScreenState.EXPRESS_SUPPLY.value

    titles = common_screen_state.get_ui_titles(ctx, screen, '模拟宇宙', '左上角标题')
    sim_uni_idx = str_utils.find_best_match_by_lcs(ScreenState.SIM_TYPE_NORMAL.value, titles)
    gold_idx = str_utils.find_best_match_by_lcs(ScreenState.SIM_TYPE_GOLD.value, titles)  # 不知道是不是游戏bug 游戏内正常的模拟宇宙也会显示这个

    if sim_uni_idx is None and gold_idx is None:
        if battle:  # 有判断的时候 不在前面的情况 就认为是战斗
            return battle_screen_state.ScreenState.BATTLE.value
        return None

    if sim_uni and str_utils.find_best_match_by_lcs(ScreenState.SIM_TYPE_NORMAL.value, titles, lcs_percent_threshold=0.51) is not None:
        return ScreenState.SIM_TYPE_NORMAL.value

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
        return battle_screen_state.ScreenState.BATTLE.value

    return None


def is_empty_to_close(ctx: SrContext, screen: MatLike) -> bool:
    """
    是否点击空白处关闭
    :param ctx: 上下文
    :param screen: 游戏画面
    :return:
    """
    return screen_utils.find_area(ctx, screen, '模拟宇宙', '点击空白处关闭') == FindAreaResultEnum.TRUE


def is_sim_uni_get_reward(ctx: SrContext, screen: MatLike) -> bool:
    """
    是否在模拟宇宙-沉浸奖励画面
    :param ctx: 上下文
    :param screen: 游戏画面
    :return:
    """
    return screen_utils.find_area(ctx, screen, '模拟宇宙', '沉浸奖励') == FindAreaResultEnum.TRUE


def in_sim_uni_choose_bless(ctx: SrContext, screen: MatLike) -> bool:
    """
    是否在模拟宇宙-选择祝福页面
    :param ctx: 上下文
    :param screen: 游戏画面
    :return:
    """
    return common_screen_state.in_secondary_ui(ctx, screen, ScreenState.SIM_BLESS.value, lcs_percent=0.55)


def in_sim_uni_choose_curio(ctx: SrContext, screen: MatLike) -> bool:
    """
    是否在模拟宇宙-选择奇物页面
    :param ctx: 上下文
    :param screen: 游戏画面
    :return:
    """
    return common_screen_state.in_secondary_ui(ctx, screen, ScreenState.SIM_CURIOS.value, lcs_percent=0.55)


def in_sim_uni_event(ctx: SrContext, screen: MatLike) -> bool:
    """
    是否在模拟宇宙-事件页面
    :param ctx: 上下文
    :param screen: 游戏画面
    :return:
    """
    return common_screen_state.in_secondary_ui(ctx, screen, ScreenState.SIM_EVENT.value)


def get_sim_uni_initial_screen_state(ctx: SrContext, screen: MatLike) -> Optional[str]:
    """
    获取模拟宇宙应用开始时的画面
    :param ctx: 上下文
    :param screen: 游戏画面
    :return:
    """
    if common_screen_state.is_normal_in_world(ctx, screen):
        level = get_level_type(ctx, screen)
        if level is not None:
            return ScreenState.SIM_UNI_REGION.value

        return ScreenState.NORMAL_IN_WORLD.value

    titles = common_screen_state.get_ui_titles(ctx, screen, '模拟宇宙', '左上角标题')

    if str_utils.find_best_match_by_lcs(ScreenState.SIM_TYPE_EXTEND.value, titles, lcs_percent_threshold=0.5) is not None:
        return ScreenState.SIM_TYPE_EXTEND.value

    if str_utils.find_best_match_by_lcs(ScreenState.SIM_TYPE_NORMAL.value, titles, lcs_percent_threshold=0.5) is not None:
        return ScreenState.SIM_TYPE_NORMAL.value

    return None

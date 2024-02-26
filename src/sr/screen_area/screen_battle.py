from enum import Enum

from basic import Rect
from sr.screen_area import ScreenArea


class ScreenBattle(Enum):

    # 战斗后
    AFTER_BATTLE_SUCCESS_1 = ScreenArea(pc_rect=Rect(820, 240, 1100, 320), text='挑战成功', lcs_percent=0.51)  # 有奖励的时候
    AFTER_BATTLE_SUCCESS_2 = ScreenArea(pc_rect=Rect(820, 205, 1100, 278), text='挑战成功', lcs_percent=0.51)  # 有双倍奖励的时候
    AFTER_BATTLE_SUCCESS_3 = ScreenArea(pc_rect=Rect(820, 320, 1100, 380), text='挑战成功', lcs_percent=0.51)  # 无奖励的时候

    AFTER_BATTLE_FAIL_1 = ScreenArea(pc_rect=Rect(820, 240, 1100, 320), text='战斗失败', lcs_percent=0.51)  # 有奖励的时候
    AFTER_BATTLE_FAIL_2 = ScreenArea(pc_rect=Rect(820, 205, 1100, 278), text='战斗失败', lcs_percent=0.51)  # 有双倍奖励的时候
    AFTER_BATTLE_FAIL_3 = ScreenArea(pc_rect=Rect(820, 320, 1100, 380), text='战斗失败', lcs_percent=0.51)  # 无奖励的时候
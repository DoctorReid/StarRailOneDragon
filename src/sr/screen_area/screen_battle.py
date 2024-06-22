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

    AFTER_BATTLE_CHALLENGE_AGAIN_BTN = ScreenArea(pc_rect=Rect(1180, 930, 1330, 960), text='再来一次')
    AFTER_BATTLE_EXIT_BTN = ScreenArea(pc_rect=Rect(544, 923, 880, 975), text='退出关卡')
    AFTER_BATTLE_CONFIRM_AGAIN_BTN = ScreenArea(pc_rect=Rect(1020, 660, 1330, 690), text='确认')

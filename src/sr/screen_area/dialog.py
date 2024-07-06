from enum import Enum

from basic import Rect
from sr.screen_area import ScreenArea


class ScreenDialog(Enum):

    # 返回登陆 对话框
    BACK_TO_LOGIN_CONFIRM = ScreenArea(pc_rect=Rect(1004, 645, 1324, 705), text='确认')

    # 快速恢复 对话框
    FAST_RECOVER_TITLE = ScreenArea(pc_rect=Rect(890, 250, 1030, 300), text='快速恢复', lcs_percent=0.5)
    FAST_RECOVER_CONFIRM = ScreenArea(pc_rect=Rect(1020, 790, 1330, 844), text='确认')
    FAST_RECOVER_CANCEL = ScreenArea(pc_rect=Rect(592, 790, 903, 844), text='取消')
    FAST_RECOVER_NO_CONSUMABLE = ScreenArea(pc_rect=Rect(1094, 554, 1266, 585), text='暂无可用消耗品')
    
    # 奇巧零食
    QUIRKY_SNACKS = ScreenArea(pc_rect=Rect(900, 300, 1450, 760), template_id="quirky_snacks", template_match_threshold=0.5)

    # 开始挑战 有角色阵亡出现的对话框
    CHALLENGE_WITH_DEAD_TITLE = ScreenArea(pc_rect=Rect(910, 400, 1020, 440), text='提示')
    CHALLENGE_WITH_DEAD_CONFIRM = ScreenArea(pc_rect=Rect(1000, 650, 1300, 700), text='确认')
    CHALLENGE_WITH_DEAD_CANCEL = ScreenArea(pc_rect=Rect(600, 650, 900, 700), text='取消', status='阵亡提示取消')

    # 开始挑战 历战回响提示次数耗尽
    CHALLENGE_ECHO_FULL_TITLE = ScreenArea(pc_rect=Rect(910, 400, 1020, 440), text='提示')
    CHALLENGE_ECHO_FULL_CONTENT = ScreenArea(pc_rect=Rect(521, 507, 1394, 551), text='本周内获取「历战回响」奖励的次数已耗尽，无法获得挑战奖励。是否继续挑战？', lcs_percent=0.5)
    CHALLENGE_ECHO_FULL_CONFIRM = ScreenArea(pc_rect=Rect(1000, 650, 1300, 700), text='确认')
    CHALLENGE_ECHO_FULL_CANCEL = ScreenArea(pc_rect=Rect(600, 650, 900, 700), text='取消', status='历战回响次数提示取消')

    # 开始挑战 不够开拓力时出现的对话框
    CHALLENGE_WITHOUT_TP_TITLE = ScreenArea(pc_rect=Rect(870, 336, 1049, 370), text='开拓力补充')
    CHALLENGE_WITHOUT_TP_CONFIRM = ScreenArea(pc_rect=Rect(1000, 650, 1300, 700), text='确认')
    CHALLENGE_WITHOUT_TP_CANCEL = ScreenArea(pc_rect=Rect(590, 707, 905, 759), text='取消')

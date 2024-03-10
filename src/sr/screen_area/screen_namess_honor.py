from enum import Enum

from basic import Rect
from sr.screen_area import ScreenArea


class ScreenNamelessHonor(Enum):

    TAB_1_CLAIM_PART = ScreenArea(pc_rect=Rect(1270, 890, 1530, 950), text='一键领取', lcs_percent=0.55)  # Tab1 - 奖励 - 一键领取
    TAB_1_DIALOG_CANCEL_BTN = ScreenArea(pc_rect=Rect(620, 970, 790, 1010), text='取消')  # Tab1 - 奖励 - 一键领取后的【取消】按钮

    TAB_2_CLAIM_PART = ScreenArea(pc_rect=Rect(1520, 890, 1810, 950), text='一键领取', lcs_percent=0.55)  # Tab2 - 任务 - 一键领取

    EMPTY_TO_CLOSE = ScreenArea(pc_rect=Rect(864, 929, 1063, 962), text='点击空白处关闭')
from enum import Enum

from basic import Rect
from sr.screen_area import ScreenArea


class ScreenSimUniEntry(Enum):
    """
    模拟宇宙入口的主页面
    """

    WEEKLY_REWARD_ICON = ScreenArea(pc_rect=Rect(360, 950, 410, 1000), template_id='ui_alert')  # 每周积分旁边的小红点
    WEEKLY_REWARD_CLAIM = ScreenArea(pc_rect=Rect(1425, 740, 1765, 782), text='一键领取')  # 领取每周积分奖励的按钮

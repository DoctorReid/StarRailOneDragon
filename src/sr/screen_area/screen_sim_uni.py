from enum import Enum

from basic import Rect
from sr.screen_area import ScreenArea


class ScreenSimUni(Enum):
    """
    模拟宇宙入口的主页面
    """

    GUIDE_TRANSPORT_1 = ScreenArea(pc_rect=Rect(1489, 523, 1616, 566), text='传送')  # 生存索引页面的传送
    GUIDE_TRANSPORT_2 = ScreenArea(pc_rect=Rect(1491, 565, 1616, 609), text='传送')  # 生存索引页面的传送 出现双倍的情况

    WEEKLY_REWARD_ICON = ScreenArea(pc_rect=Rect(360, 950, 410, 1000), template_id='ui_alert')  # 每周积分旁边的小红点
    WEEKLY_REWARD_CLAIM = ScreenArea(pc_rect=Rect(1425, 740, 1765, 782), text='一键领取')  # 领取每周积分奖励的按钮

    GOING_1 = ScreenArea(pc_rect=Rect(813, 484, 888, 511), text='进行中')
    GOING_2 = ScreenArea(pc_rect=Rect(813, 505, 888, 540), text='进行中')
    CURRENT_NUM_1 = ScreenArea(pc_rect=Rect(805, 515, 945, 552))
    CURRENT_NUM_2 = ScreenArea(pc_rect=Rect(805, 546, 945, 583))

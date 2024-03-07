from enum import Enum

from basic import Rect
from sr.screen_area import ScreenArea


class ScreenSimUni(Enum):

    # 指南部分
    GUIDE_TRANSPORT_1 = ScreenArea(pc_rect=Rect(1489, 523, 1616, 566), text='传送')  # 生存索引页面的传送
    GUIDE_TRANSPORT_2 = ScreenArea(pc_rect=Rect(1491, 565, 1616, 609), text='传送')  # 生存索引页面的传送 出现双倍的情况

    # 入口选择宇宙画面
    WEEKLY_REWARD_ICON = ScreenArea(pc_rect=Rect(360, 950, 410, 1000), template_id='ui_alert')  # 每周积分旁边的小红点
    WEEKLY_REWARD_CLAIM = ScreenArea(pc_rect=Rect(1425, 740, 1765, 782), text='一键领取')  # 领取每周积分奖励的按钮

    GOING_1 = ScreenArea(pc_rect=Rect(813, 484, 888, 511), text='进行中')
    GOING_2 = ScreenArea(pc_rect=Rect(813, 505, 888, 540), text='进行中')
    CURRENT_NUM_1 = ScreenArea(pc_rect=Rect(805, 515, 945, 552))  # 当前宇宙名称
    CURRENT_NUM_2 = ScreenArea(pc_rect=Rect(805, 546, 945, 583))  # 当前宇宙名称

    # 楼层中画面
    EXIT_BTN = ScreenArea(pc_rect=Rect(0, 0, 75, 115), template_id='ui_icon_10', status='模拟宇宙可移动画面', pc_alt=True)  # 左上方 退出按钮
    MENU_EXIT = ScreenArea(pc_rect=Rect(1323, 930, 1786, 985), text='结束并结算')
    BATTLE_EXIT = ScreenArea(pc_rect=Rect(1038, 962, 1391, 1013), text='终止战斗并结算')
    EXIT_DIALOG_CONFIRM = ScreenArea(pc_rect=Rect(1022, 651, 1324, 697), text='确认')
    LEVEL_TYPE = ScreenArea(pc_rect=Rect(52, 13, 276, 40))  # 左上角楼层类型

    # 结算画面
    EXIT_EMPTY_TO_CONTINUE = ScreenArea(pc_rect=Rect(869, 899, 1057, 928), text='点击空白处继续')

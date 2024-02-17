from enum import Enum

from basic import Rect
from sr.screen_area import ScreenArea


class ScreenTreasuresLightWard(Enum):

    # 【指南】-【逐光捡金】 画面
    TL_CATEGORY_FORGOTTEN_HALL = ScreenArea(pc_rect=Rect(280, 435, 670, 535), text='忘却之庭')
    TL_CATEGORY_PURE_FICTION = ScreenArea(pc_rect=Rect(280, 570, 670, 670), text='虚构叙事')

    TL_SCHEDULE_1_TRANSPORT = ScreenArea(pc_rect=Rect(1488, 648, 1613, 686), text='传送')
    TL_SCHEDULE_2_TRANSPORT = ScreenArea(pc_rect=Rect(1488, 882, 1613, 920), text='传送')

    TL_SCHEDULE_1_NAME = ScreenArea(pc_rect=Rect(927, 556, 1417, 587))
    TL_SCHEDULE_2_NAME = ScreenArea(pc_rect=Rect(927, 786, 1417, 820))

    # 【忘却之庭】画面
    FH_TOTAL_STAR = ScreenArea(pc_rect=Rect(1665, 950, 1725, 995))  # 右下角 总星数

    # 【虚构叙事】画面
    PF_TITLE = ScreenArea(pc_rect=Rect(160, 63, 262, 90), text='虚构叙事')  # 左上角标题

    # 公共 - 大世界画面
    EXIT_BTN = ScreenArea(pc_rect=Rect(0, 0, 75, 115), template_id='ui_icon_10', status='大世界')  # 左上方 退出按钮

    # 公共战斗结束
    AFTER_BATTLE_SUCCESS_1 = ScreenArea(pc_rect=Rect(820, 200, 1100, 270), text='挑战成功', lcs_percent=0.3)  # 有奖励 战斗中画面可能会错误识别到字体 需要稍微提高阈值
    AFTER_BATTLE_SUCCESS_2 = ScreenArea(pc_rect=Rect(820, 300, 1100, 370), text='挑战成功', lcs_percent=0.3)  # 无奖励
    AFTER_BATTLE_FAIL = ScreenArea(pc_rect=Rect(785, 230, 1155, 320), text='战斗失败', lcs_percent=0.3)

    AFTER_BATTLE_BACK_BTN_1 = ScreenArea(pc_rect=Rect(630, 920, 870, 975), text='返回逐光捡金')
    AFTER_BATTLE_BACK_BTN_2 = ScreenArea(pc_rect=Rect(790, 920, 1140, 975), text='返回逐光捡金')

    AFTER_BATTLE_QUICK_PASS_TITLE = ScreenArea(pc_rect=Rect(865, 81, 1061, 131), text='快速通关')
    AFTER_BATTLE_QUICK_PASS_CONFIRM = ScreenArea(pc_rect=Rect(800, 960, 1122, 1010), text='确认')
    AFTER_BATTLE_QUICK_PASS_EMPTY = ScreenArea(pc_rect=Rect(868, 930, 1053, 960), text='点击空白处关闭')

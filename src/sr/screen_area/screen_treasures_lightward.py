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
    FH_TITLE = ScreenArea(pc_rect=Rect(102, 36, 185, 63), text='忘却之庭')  # 左上角标题
    FH_TOTAL_STAR = ScreenArea(pc_rect=Rect(1665, 950, 1725, 995))  # 右下角 总星数
    FH_START_CHALLENGE = ScreenArea(pc_rect=Rect(1500, 960, 1840, 1010), text='混沌回忆')

    FH_AFTER_BATTLE_SUCCESS_1 = ScreenArea(pc_rect=Rect(820, 200, 1100, 270), text='挑战成功', lcs_percent=0.3)  # 有奖励 战斗中画面可能会错误识别到字体 需要稍微提高阈值
    FH_AFTER_BATTLE_SUCCESS_2 = ScreenArea(pc_rect=Rect(820, 300, 1100, 370), text='挑战成功', lcs_percent=0.3)  # 无奖励
    FH_AFTER_BATTLE_FAIL = ScreenArea(pc_rect=Rect(785, 230, 1155, 320), text='战斗失败', lcs_percent=0.3)

    FH_AFTER_BATTLE_BACK_BTN_1 = ScreenArea(pc_rect=Rect(630, 920, 870, 975), text='返回逐光捡金')
    FH_AFTER_BATTLE_BACK_BTN_2 = ScreenArea(pc_rect=Rect(790, 920, 1140, 975), text='返回逐光捡金')

    # 【虚构叙事】画面
    PF_TITLE = ScreenArea(pc_rect=Rect(160, 63, 262, 90), text='虚构叙事')  # 左上角标题
    PF_CACOPHONY_NODE_1 = ScreenArea(pc_rect=Rect(1775, 717, 1873, 792))  # 节点1-增益效果
    PF_CACOPHONY_NODE_2 = ScreenArea(pc_rect=Rect(1775, 823, 1873, 909))  # 节点2-增益效果
    PF_CACOPHONY_OPT_1 = ScreenArea(pc_rect=Rect(806, 177, 870, 224))  # 增益效果选项1
    PF_CACOPHONY_OPT_2 = ScreenArea(pc_rect=Rect(806, 354, 870, 384))  # 增益效果选项2
    PF_CACOPHONY_OPT_3 = ScreenArea(pc_rect=Rect(806, 523, 870, 554))  # 增益效果选项3
    PF_CACOPHONY_CONFIRM = ScreenArea(pc_rect=Rect(1515, 960, 1865, 1009), text='装配效果')
    PF_START_CHALLENGE = ScreenArea(pc_rect=Rect(1500, 960, 1840, 1010), text='进入故事')

    PF_AFTER_BATTLE_SUCCESS_1 = ScreenArea(pc_rect=Rect(820, 200, 1100, 270), text='挑战成功', lcs_percent=0.3)  # 有奖励 战斗中画面可能会错误识别到字体 需要稍微提高阈值
    PF_AFTER_BATTLE_SUCCESS_2 = ScreenArea(pc_rect=Rect(820, 245, 1100, 307), text='挑战成功', lcs_percent=0.3)  # 无奖励
    PF_AFTER_BATTLE_FAIL = ScreenArea(pc_rect=Rect(836, 312, 1088, 380), text='战斗失败', lcs_percent=0.3)

    PF_AFTER_BATTLE_BACK_BTN = ScreenArea(pc_rect=Rect(788, 979, 1121, 1035), text='返回虚构叙事')  # 成功失败都是同一个

    # 公共 - 大世界画面
    EXIT_BTN = ScreenArea(pc_rect=Rect(0, 0, 75, 115), template_id='ui_icon_10', status='逐光捡金可移动画面', pc_alt=True)  # 左上方 退出按钮
    NODE_FIRST_CLICK_EMPTY = ScreenArea(pc_rect=Rect(856, 851, 1071, 885), text='点击空白处关闭')

    # 公共战斗结束
    AFTER_BATTLE_QUICK_PASS_TITLE = ScreenArea(pc_rect=Rect(865, 81, 1061, 131), text='快速通关')
    AFTER_BATTLE_QUICK_PASS_CONFIRM = ScreenArea(pc_rect=Rect(800, 960, 1122, 1010), text='确认')
    AFTER_BATTLE_QUICK_PASS_EMPTY = ScreenArea(pc_rect=Rect(868, 930, 1053, 960), text='点击空白处关闭')

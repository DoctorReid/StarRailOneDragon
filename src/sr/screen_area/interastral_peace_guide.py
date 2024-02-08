from enum import Enum

from basic import Rect
from sr.screen_area import ScreenArea


class ScreenGuide(Enum):

    GUIDE_TITLE = ScreenArea(pc_rect=Rect(98, 39, 350, 100), text='星级和平指南')  # 一级标题 TODO 未细化

    # 指南上方的页签
    GUIDE_TAB_1 = ScreenArea(pc_rect=Rect(300, 170, 430, 245))  # 行动摘要
    GUIDE_TAB_2 = ScreenArea(pc_rect=Rect(430, 170, 545, 245))  # 每日实训
    GUIDE_TAB_3 = ScreenArea(pc_rect=Rect(545, 170, 650, 245))  # 生存索引
    GUIDE_TAB_4 = ScreenArea(pc_rect=Rect(650, 170, 780, 245))  # 逐光捡金
    GUIDE_TAB_5 = ScreenArea(pc_rect=Rect(780, 170, 900, 245))  # 战术训练

    # 生存索引部分
    SURVIVAL_INDEX_TITLE = ScreenArea(pc_rect=Rect(98, 39, 350, 100), text='生存索引')  # 二级标题 TODO 未细化
    SURVIVAL_INDEX_CATE = ScreenArea(pc_rect=Rect(270, 300, 680, 910))  # 左边类目区域
    SURVIVAL_INDEX_TRANSPORT = ScreenArea(pc_rect=Rect(270, 300, 680, 910))  # 右边传送一列的位置
from enum import Enum

from basic import Rect
from sr.const import map_const
from sr.screen_area import ScreenArea


class ScreenGuide(Enum):

    EXIT_BTN = ScreenArea(pc_rect=Rect(1835, 40, 1890, 95))  # 右上角退出按钮

    GUIDE_TITLE = ScreenArea(pc_rect=Rect(98, 39, 350, 100), text='星级和平指南')  # 一级标题 TODO 未细化

    # 指南上方的页签
    GUIDE_TAB_1 = ScreenArea(pc_rect=Rect(300, 170, 430, 245))  # 行动摘要
    GUIDE_TAB_2 = ScreenArea(pc_rect=Rect(430, 170, 545, 245))  # 每日实训
    GUIDE_TAB_3 = ScreenArea(pc_rect=Rect(545, 170, 650, 245))  # 生存索引
    GUIDE_TAB_4 = ScreenArea(pc_rect=Rect(650, 170, 780, 245))  # 逐光捡金
    GUIDE_TAB_5 = ScreenArea(pc_rect=Rect(780, 170, 900, 245))  # 战术训练

    # 指南右侧的副本列表
    MISSION_LIST_RECT = ScreenArea(pc_rect=Rect(695, 295, 1655, 930))

    # 拟造花萼金-二级分类
    BUD_1_SUB_CATE_1 = ScreenArea(pc_rect=Rect(728, 297, 861, 356), text=map_const.P02.cn)
    BUD_1_SUB_CATE_2 = ScreenArea(pc_rect=Rect(861, 297, 993, 356), text=map_const.P03.cn)
    BUD_1_SUB_CATE_3 = ScreenArea(pc_rect=Rect(997, 297, 1123, 356), text=map_const.P04.cn)

    # 生存索引部分
    SURVIVAL_INDEX_TITLE = ScreenArea(pc_rect=Rect(98, 39, 350, 100), text='生存索引')  # 二级标题 TODO 未细化
    SURVIVAL_INDEX_CATE = ScreenArea(pc_rect=Rect(270, 300, 680, 910))  # 左边类目区域
    SURVIVAL_INDEX_TRANSPORT = ScreenArea(pc_rect=Rect(270, 300, 680, 910))  # 右边传送一列的位置

    # 饰品提取
    OE_DIFF_DROPDOWN = ScreenArea(pc_rect=Rect(98, 39, 350, 100))  # 难度下拉框
    OE_DIFF_DROPDOWN_OPTIONS = ScreenArea(pc_rect=Rect(98, 39, 350, 100))  # 难度列表
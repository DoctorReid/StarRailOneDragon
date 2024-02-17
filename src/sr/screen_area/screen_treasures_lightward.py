from enum import Enum

from basic import Rect
from sr.screen_area import ScreenArea


class ScreenTreasuresLightWard(Enum):

    # 【指南】-【逐光捡金】 画面
    TL_CATEGORY_FORGOTTEN_HALL = ScreenArea(pc_rect=Rect(280, 435, 670, 535), text='忘却之庭')
    TL_CATEGORY_STORY = ScreenArea(pc_rect=Rect(280, 570, 670, 670), text='虚构叙事')

    TL_SCHEDULE_1_TRANSPORT = ScreenArea(pc_rect=Rect(1488, 648, 1613, 686), text='传送')
    TL_SCHEDULE_2_TRANSPORT = ScreenArea(pc_rect=Rect(1488, 882, 1613, 920), text='传送')

    TL_SCHEDULE_1_NAME = ScreenArea(pc_rect=Rect(927, 556, 1417, 587))
    TL_SCHEDULE_2_NAME = ScreenArea(pc_rect=Rect(927, 786, 1417, 820))

    # 【混沌回忆】画面
    CM_TOTAL_STAR = ScreenArea(pc_rect=Rect(1665, 950, 1725, 995))  # 右下角 总星数
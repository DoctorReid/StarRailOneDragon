from basic import Rect


class GuideTab:

    def __init__(self, cn: str, num: int, rect: Rect):

        self.cn: str = cn
        """中文"""

        self.num: int = num
        """TAB顺序"""

        self.rect: Rect = rect
        """按钮位置"""


GUIDE_TAB_1 = GuideTab(cn='行动摘要', num=1, rect=Rect(280, 178, 402, 245))
GUIDE_TAB_2 = GuideTab(cn='每日实训', num=2, rect=Rect(402, 178, 526, 245))
GUIDE_TAB_3 = GuideTab(cn='生存索引', num=3, rect=Rect(526, 178, 640, 245))
GUIDE_TAB_4 = GuideTab(cn='战术训练', num=4, rect=Rect(640, 178, 761, 245))



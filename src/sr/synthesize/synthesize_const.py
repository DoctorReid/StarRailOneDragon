from enum import Enum

from basic import Rect
from sr.screen_area import ScreenArea


class ScreenSynthesize(Enum):

    TITLE = ScreenArea(pc_rect=Rect(), text='合成')  # 左上角标题
    CATEGORY_TITLE = ScreenArea(pc_rect=Rect())  # 左上角二级标题

    CATEGORY_1_BTN = ScreenArea(pc_rect=Rect())  # 合成类别1 - 消耗品
    CATEGORY_2_BTN = ScreenArea(pc_rect=Rect())  # 合成类别2 - 消耗品
    CATEGORY_3_BTN = ScreenArea(pc_rect=Rect())  # 合成类别3 - 消耗品
    CATEGORY_4_BTN = ScreenArea(pc_rect=Rect())  # 合成类别4 - 消耗品

    ITEM_LIST = ScreenArea(pc_rect=Rect())  # 合成物品的列表

    NOT_ENOUGH_MATERIAL = ScreenArea(pc_rect=Rect(), text='合成所需材料不足')
    NUM_MAX = ScreenArea(pc_rect=Rect())  # 合成数量最大值

    SYNTHESIZE_BTN = ScreenArea(pc_rect=Rect(), text='合成')  # 合成按钮
    SYNTHESIZE_DIALOG_CONFIRM = ScreenArea(pc_rect=Rect(1020, 790, 1330, 844), text='确认')  # 合成弹窗的确认
    SYNTHESIZE_EMPTY_TO_CLOSE = ScreenArea(pc_rect=Rect(868, 930, 1053, 960), text='点击空白处关闭')


class SynthesizeCategory:

    def __init__(self, name: str, area: ScreenArea):
        self.name: str = name
        self.area: ScreenArea = area


class SynthesizeCategoryEnum(Enum):

    CONSUMABLE = SynthesizeCategory('消耗品', ScreenSynthesize.CATEGORY_1_BTN.value)


class SynthesizeItem:

    def __init__(self, category_id: str, name: str, template_id: str):
        self.category: SynthesizeCategory = SynthesizeCategoryEnum[category_id.upper()].value
        self.name: str = name
        self.template_id: str = template_id


class SynthesizeItemEnum(Enum):

    QUICK_SNACK = SynthesizeItem(SynthesizeCategoryEnum.CONSUMABLE.name, '奇巧零食', 'quick_snack')

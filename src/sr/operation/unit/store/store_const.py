from enum import Enum

from basic import Rect
from sr.screen_area import ScreenArea


class ScreenStore(Enum):

    STORE_ITEM_LIST = ScreenArea(pc_rect=Rect(290, 110, 1790, 817))  # 商品列表

    # 购买对话框
    BUY_DIALOG_MAX_BTN = ScreenArea(pc_rect=Rect(1400, 600, 1500, 660),
                                    template_id='store_buy_max', template_sub_dir='store')  # 最大值
    BUY_DIALOG_ADD_BTN = ScreenArea(pc_rect=Rect(1330, 600, 1430, 660),
                                    template_id='store_buy_add', template_sub_dir='store')  # 增加一件
    BUY_DIALOG_SOLD_OUT = ScreenArea(pc_rect=Rect(830, 659, 1110, 692), text='已售罄')
    BUY_DIALOG_NO_MONEY = ScreenArea(pc_rect=Rect(830, 659, 1110, 692), text='兑换材料不足')
    BUY_DIALOG_CANCEL_BTN = ScreenArea(pc_rect=Rect(592, 714, 909, 769), text='取消')
    BUY_DIALOG_CONFIRM_BTN = ScreenArea(pc_rect=Rect(1011, 714, 1324, 769), text='确认')


class StoreItem:

    def __init__(self, template_id: str, cn: str):
        """
        商品商品
        :param template_id:
        :param cn:
        """
        self.template_id: str = template_id  # 模板ID
        self.cn: str = cn  # 商品名称


class StoreItemEnum(Enum):

    GASEOUS_LIQUID = StoreItem('gaseous_liquid', '气态流体')
    SEED = StoreItem('seed', '种子')
    XIANZHOU_PARCEL = StoreItem('xianzhou_parcel', '逾期未取的贵重邮包')

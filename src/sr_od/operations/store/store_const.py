from enum import Enum


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

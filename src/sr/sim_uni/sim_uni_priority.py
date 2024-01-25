from typing import List, Optional


class SimUniAllPriority:

    def __init__(self, bless_id_list_1: Optional[List[str]] = None, bless_id_list_2: Optional[List[str]] = None,
                 curio_id_list: Optional[List[str]] = None, next_level_id_list: Optional[List[str]] = None):
        """
        模拟宇宙中使用的优先级
        :param bless_id_list_1: 祝福第一优先级
        :param bless_id_list_2: 祝福第二优先级
        :param curio_id_list: 奇物优先级
        :param next_level_id_list: 楼层优先级
        """
        self.bless_id_list_1: List[str] = bless_id_list_1 or []
        self.bless_id_list_2: List[str] = bless_id_list_2 or []
        self.curio_id_list: List[str] = curio_id_list or []
        self.next_level_id_list: List[str] = next_level_id_list or []

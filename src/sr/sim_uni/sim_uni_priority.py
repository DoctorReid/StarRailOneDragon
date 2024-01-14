from typing import List


class SimUniBlessPriority:

    def __init__(self,
                 first_path: str,
                 ):
        self.first_path: str = first_path
        """第一优先命途"""


class SimUniNextLevelPriority:

    def __init__(self,
                 first_type_id: str):
        self.first_type_id: str = first_type_id


class SimUniCurioPriority:

    def __init__(self, curio_names: List[str]):
        """
        奇物的优先级
        :param curio_names:
        """
        self.order_name_list: List[str] = curio_names

import os
from typing import List

from basic import os_utils
from basic.config import ConfigHolder


class WorldPatrolWhitelist(ConfigHolder):

    def __init__(self, file_name: str):
        self.id: str = file_name
        super().__init__(file_name, sample=False, sub_dir=['world_patrol', 'whitelist'])

    @property
    def valid(self) -> bool:
        return self.type in ['white', 'black'] and len(self.list) > 0

    @property
    def type(self) -> str:
        return self.get('type', 'black')

    @type.setter
    def type(self, new_value: str):
        self.update('type', new_value)

    @property
    def name(self) -> str:
        return self.get('name', '未命名')

    @name.setter
    def name(self, new_value: str):
        self.update('name', new_value)

    @property
    def list(self) -> List[str]:
        return self.get('list', [])

    @list.setter
    def list(self, new_value: List[str]):
        self.update('list', new_value)


def load_all_whitelist_id() -> List[str]:
    """
    加载所有名单
    :return:
    """
    whitelist_id_arr: List[str] = []
    dir_path = os_utils.get_path_under_work_dir('config', 'world_patrol', 'whitelist')
    for filename in os.listdir(dir_path):
        idx = filename.find('.yml')
        if idx == -1:
            continue
        whitelist_id_arr.append(filename[0:idx])

    return whitelist_id_arr

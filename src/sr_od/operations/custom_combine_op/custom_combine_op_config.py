import os
import yaml
from typing import List

from one_dragon.utils import os_utils


class CustomCombineOpItem:

    def __init__(self, op: str, data: List[str], allow_fail: bool):
        self.op: str = op  # 指令ID
        self.data: List[str] = data  # 输入指令的数据
        self.allow_fail: bool = allow_fail  # 该指令允许失败


class CustomCombineOpConfig:

    def __init__(self, config_file_name: str):
        self.config_file_name: str = config_file_name  # 配置文件名 没有yml的后缀
        self.existed: bool = False  # 是否存在配置文件

        self.config_name: str = ''
        self.ops: List[CustomCombineOpItem] = []

        self.read_from_file()

    @property
    def yml_file_path(self) -> str:
        """
        配置文件的目录
        :return:
        """
        dir_path = os_utils.get_path_under_work_dir('config', 'custom_combine_op')
        return os.path.join(dir_path, '%s.yml' % self.config_file_name)

    def read_from_file(self):
        file_path = self.yml_file_path
        self.existed = os.path.exists(file_path)
        if self.existed:
            with open(file_path, 'r', encoding='utf-8') as file:
                yaml_data = yaml.safe_load(file)
                self.init_from_yaml_data(yaml_data)

    def init_from_yaml_data(self, yaml_data: dict):
        self.config_name = yaml_data.get('name', '')
        ops = yaml_data.get('ops', [])
        for op_item in ops:
            self.ops.append(CustomCombineOpItem(op_item['op'], op_item['data'],
                                                allow_fail=op_item.get('allow_fail', False)
                                                ))

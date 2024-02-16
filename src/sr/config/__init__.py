import os
from typing import List

from basic import config_utils


class ConfigHolder:

    def __init__(self, module_name: str, sample: bool = True, sub_dir: List[str] = None, mock: bool = False):
        self.mod = module_name
        self.sample = sample
        self.sub_dir = sub_dir
        self.data: dict = {}
        self.mock: bool = mock  # 不读取文件
        self.refresh()

    def refresh(self):
        self._read_config()
        self._init_after_read_file()

    def _read_config(self):
        if self.sample:  # 脚本更新时 可能加入了新配置 要从sample同步过去
            self.data = config_utils.async_sample(self.mod, sub_dir=self.sub_dir)
        else:
            self.data = config_utils.read_config(self.mod, sample=self.sample, sub_dir=self.sub_dir)
            if self.data is None:
                self.data = {}

    def save(self):
        if self.mock:
            return
        config_utils.save_config(self.mod, self.data, sub_dir=self.sub_dir)

    def save_diy(self, text: str):
        """
        保存自定义的文本
        :param text:
        :return:
        """
        if self.mock:
            return

        file_path = config_utils.get_config_file_path(self.mod, sub_dir=self.sub_dir)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(text)

    def _init_after_read_file(self):
        pass

    def get(self, prop: str, value=None):
        return self.data[prop] if prop in self.data else value

    def update(self, key: str, value, save: bool = True):
        if self.data is None:
            self.data = {}
        self.data[key] = value
        if save:
            self.save()

    def delete(self):
        """
        删除配置文件
        :return:
        """
        path = config_utils.get_config_file_path(self.mod, sub_dir=self.sub_dir)
        os.remove(path)

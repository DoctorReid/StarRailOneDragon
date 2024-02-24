import os
from typing import Optional, List

from basic import config_utils


class ConfigHolder:

    def __init__(self, module_name: str,
                 script_account_idx: Optional[int] = None,
                 sample: bool = True, sub_dir: Optional[List[str]] = None, mock: bool = False):
        self.mod: str = module_name
        self.script_account_idx: Optional[int] = script_account_idx
        self.sample: bool = sample
        self.sub_dir: Optional[List[str]] = sub_dir
        self.data: dict = {}
        self.mock: bool = mock  # 不读取文件
        self.refresh()

    def refresh(self):
        self._read_config()
        self._init_after_read_file()

    def _read_config(self):
        if self.sample:  # 脚本更新时 可能加入了新配置 要从sample同步过去
            self.data = config_utils.read_config_with_sample(self.mod,
                                                             script_account_idx=self.script_account_idx,
                                                             sub_dir=self.sub_dir)
        else:
            self.data = config_utils.read_config(self.mod,
                                                 script_account_idx=self.script_account_idx,
                                                 sub_dir=self.sub_dir)
        if self.data is None:
            self.data = {}

    def save(self):
        if self.mock:
            return
        config_utils.save_config(self.data, self.mod,
                                 script_account_idx=self.script_account_idx,
                                 sub_dir=self.sub_dir)

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
        os.remove(self.config_file_path)

    @property
    def config_file_path(self) -> str:
        return config_utils.get_config_file_path(self.mod, sub_dir=self.sub_dir)

    def move_to_account_idx(self, script_account_idx: int):
        """
        将当前配置移动到对应的脚本账号中
        :return:
        """
        self.delete()  # 删除旧的配置
        self.script_account_idx = script_account_idx
        self.save()  # 保存新的配置

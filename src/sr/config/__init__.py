from typing import List

from basic import config_utils


class ConfigHolder:

    def __init__(self, module_name: str, sample: bool = True, sub_dir: List[str] = None):
        self.mod = module_name
        self.sample = sample
        self.sub_dir = sub_dir
        self.data: dict = {}
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
        config_utils.save_config(self.mod, self.data, sub_dir=self.sub_dir)

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

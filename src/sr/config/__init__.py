from typing import List

from basic import config_utils


class ConfigHolder:

    def __init__(self, module_name: str, sample: bool = True, sub_dir: List[str] = None):
        self.mod = module_name
        self.sample = sample
        self.sub_dir = sub_dir
        self.data = None
        self.refresh()

    def refresh(self):
        self.read_config()
        self.init()

    def read_config(self):
        if self.sample:  # 脚本更新时 可能加入了新配置 要从sample同步过去
            self.data = config_utils.async_sample(self.mod, sub_dir=self.sub_dir)
        else:
            self.data = config_utils.read_config(self.mod, sample=self.sample, sub_dir=self.sub_dir)

    def write_config(self):
        config_utils.save_config(self.mod, self.data, sub_dir=self.sub_dir)

    def init(self):
        pass

    def get(self, prop: str):
        return self.data[prop] if prop in self.data else None

    def update(self, key: str, value):
        if self.data is None:
            self.data = {}
        self.data[key] = value

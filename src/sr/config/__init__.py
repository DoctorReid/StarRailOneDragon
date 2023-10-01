from basic import config_utils


class ConfigHolder:

    def __init__(self, module_name: str, sample: bool = True, sub_dir: str = None):
        self.mod = module_name
        self.sample = sample
        self.sub_dir = sub_dir
        self.data = None
        self.refresh()

    def refresh(self):
        self.read_config()
        self.init()

    def read_config(self):
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
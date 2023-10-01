from basic import config_utils


class ConfigHolder:

    def __init__(self, module_name: str):
        self.mod = module_name
        self.data = None
        self.refresh()

    def refresh(self):
        self.read_config()
        self.init()

    def read_config(self):
        self.data = config_utils.read_config(self.mod)

    def write_config(self):
        config_utils.save_config(self.mod, self.data)

    def init(self):
        pass

    def get(self, prop: str):
        return self.data[prop] if prop in self.data else None

    def update(self, key: str, value):
        self.data[key] = value
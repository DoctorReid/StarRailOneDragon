from sr.config import ConfigHolder
from sr.const import game_config_const


class MiniMapPos:

    def __init__(self, x, y, r):
        # 原点
        self.x = int(x)
        self.y = int(y)
        self.r = int(r)
        # 矩形左上角
        self.lx = self.x - self.r - 3
        self.ly = self.y - self.r - 3
        # 矩形右下角
        self.rx = self.x + self.r + 3
        self.ry = self.y + self.r + 3

    def __str__(self):
        return "(%d, %d) %.2f" % (self.x, self.y, self.r)


class GameConfig(ConfigHolder):

    def __init__(self):
        self.mini_map_pos: MiniMapPos = None
        self.server_region: str = game_config_const.SERVER_REGION_CN
        self.run_mode: int = game_config_const.RUN_MODE_OFF
        super().__init__('game')

    def init(self):
        mini_map = self.data['mini_map']
        self.mini_map_pos = MiniMapPos(mini_map['x'], mini_map['y'], mini_map['r'])

        if self.data.get('server_region') in game_config_const.SERVER_TIME_OFFSET:
            self.server_region = self.data.get('server_region')

        if self.data.get('run_mode') in game_config_const.RUN_MODE.values():
            self.run_mode = self.data.get('run_mode')

    def set_server_region(self, value: str):
        self.server_region = value
        self.update('server_region', value)

    def set_run_mode(self, value: int):
        self.run_mode = value
        self.update('run_mode', value)


_gc = None


def get() -> GameConfig:
    global _gc
    if _gc is None:
        _gc = GameConfig()

    return _gc



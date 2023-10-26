from sr.config import ConfigHolder


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
        super().__init__('game')

    def init(self):
        mini_map = self.data['mini_map']
        self.mini_map_pos = MiniMapPos(mini_map['x'], mini_map['y'], mini_map['r'])


_game_config = None


def get() -> GameConfig:
    global _game_config
    if _game_config is None:
        _game_config = GameConfig()

    return _game_config



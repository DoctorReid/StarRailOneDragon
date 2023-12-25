from typing import Optional

from sr.config import ConfigHolder
from sr.const import game_config_const, ocr_const
from sr.const.game_config_const import SERVER_REGION_CN


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
        self.mini_map_pos: Optional[MiniMapPos] = None
        super().__init__('game')

    def _init_after_read_file(self):
        mini_map = self.data['mini_map']
        self.mini_map_pos = MiniMapPos(mini_map['x'], mini_map['y'], mini_map['r'])

    @property
    def server_region(self) -> str:
        """
        游戏区服
        :return:
        """
        return self.get('server_region', game_config_const.SERVER_REGION_CN)

    @server_region.setter
    def server_region(self, new_value: str):
        """
        更新游戏区服
        :return:
        """
        self.update('server_region', new_value)

    @property
    def run_mode(self) -> str:
        """
        疾跑模式
        :return:
        """
        return self.get('run_mode', game_config_const.RUN_MODE_OFF)

    @run_mode.setter
    def run_mode(self, new_value: str):
        """
        更新疾跑模式
        :return:
        """
        self.update('run_mode', new_value)

    @property
    def lang(self) -> str:
        """
        游戏语言
        :return:
        """
        return self.get('lang', game_config_const.LANG_CN)

    @lang.setter
    def lang(self, new_value: str):
        """
        更新游戏语言
        :return:
        """
        self.update('lang', new_value)

    @property
    def game_path(self) -> str:
        """
        游戏路径
        :return:
        """
        return self.get('game_path', '')

    @game_path.setter
    def game_path(self, new_value: str):
        """
        更新游戏路径
        :return:
        """
        self.update('game_path', new_value)

    @property
    def planet_lcs_percent(self):
        return ocr_const.PLANET_LCS_PERCENT[self.lang]

    @property
    def region_lcs_percent(self):
        return ocr_const.REGION_LCS_PERCENT[self.lang]

    @property
    def special_point_lcs_percent(self):
        return ocr_const.SPECIAL_POINT_LCS_PERCENT[self.lang]

    @property
    def character_name_lcs_percent(self):
        return ocr_const.CHARACTER_NAME_LCS_PERCENT[self.lang]

    @property
    def proxy_type(self) -> str:
        """
        代理类型
        :return:
        """
        return self.get('proxy_type', 'ghproxy')

    @proxy_type.setter
    def proxy_type(self, new_value: str):
        """
        更新代理类型
        :return:
        """
        self.update('proxy_type', new_value)

    @property
    def personal_proxy(self) -> str:
        """
        代理类型
        :return:
        """
        return self.get('personal_proxy', '')

    @personal_proxy.setter
    def personal_proxy(self, new_value: str):
        """
        更新代理类型
        :return:
        """
        self.update('personal_proxy', new_value)

    @property
    def proxy_address(self) -> Optional[str]:
        """
        :return: 真正使用的代理地址
        """
        proxy_type = self.proxy_type
        if proxy_type == game_config_const.PROXY_TYPE_NONE.id:
            return None
        elif proxy_type == game_config_const.PROXY_TYPE_GHPROXY.id:
            return game_config_const.GH_PROXY_URL
        elif proxy_type == game_config_const.PROXY_TYPE_PERSONAL.id:
            proxy = self.personal_proxy
            return None if proxy == '' else proxy
        return None

    @property
    def key_interact(self) -> str:
        """
        交互按钮
        :return:
        """
        return self.get('key_interact', 'f')

    @key_interact.setter
    def key_interact(self, new_value):
        """
        更新交互按钮
        :return:
        """
        self.update('key_interact', new_value)

    @property
    def key_technique(self) -> str:
        """
        秘技按钮
        :return:
        """
        return self.get('key_technique', 'e')

    @key_technique.setter
    def key_technique(self, new_value):
        """
        更新秘技按钮
        :return:
        """
        self.update('key_technique', new_value)

    @property
    def key_open_map(self) -> str:
        """
        秘技按钮
        :return:
        """
        return self.get('key_open_map', 'm')

    @key_open_map.setter
    def key_open_map(self, new_value):
        """
        更新秘技按钮
        :return:
        """
        self.update('key_open_map', new_value)

    @property
    def key_esc(self) -> str:
        """
        秘技按钮
        :return:
        """
        return self.get('key_esc', 'esc')

    @key_esc.setter
    def key_esc(self, new_value):
        """
        更新秘技按钮
        :return:
        """
        self.update('key_esc', new_value)


_gc = None


def get() -> GameConfig:
    global _gc
    if _gc is None:
        _gc = GameConfig()

    return _gc



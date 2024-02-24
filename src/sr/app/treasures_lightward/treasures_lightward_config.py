from typing import List, Optional

from basic.config import ConfigHolder
from sr.app.app_description import AppDescriptionEnum
from sr.treasures_lightward.treasures_lightward_team_module import TreasuresLightwardTeamModule


class TreasuresLightwardConfig(ConfigHolder):

    def __init__(self, account_idx: Optional[int] = None):
        ConfigHolder.__init__(self, AppDescriptionEnum.TREASURES_LIGHTWARD.value.id, account_idx=account_idx)

    def _init_after_read_file(self):
        pass

    @property
    def team_module_list(self) -> List[TreasuresLightwardTeamModule]:
        arr = self.get('team_module_list', [])
        ret = []
        for i in arr:
            ret.append(TreasuresLightwardTeamModule(**i))
        return ret

    @team_module_list.setter
    def team_module_list(self, new_list: List[TreasuresLightwardTeamModule]):
        dict_arr = []
        for i in new_list:
            dict_arr.append(vars(i))
        self.update('team_module_list', dict_arr)


_treasures_lightward_config: Optional[TreasuresLightwardConfig] = None


def get_config() -> TreasuresLightwardConfig:
    global _treasures_lightward_config
    if _treasures_lightward_config is None:
        _treasures_lightward_config = TreasuresLightwardConfig()
    return _treasures_lightward_config

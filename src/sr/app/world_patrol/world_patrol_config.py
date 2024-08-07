from typing import Optional

from basic.config import ConfigHolder
from sr.app.app_description import AppDescriptionEnum


class WorldPatrolConfig(ConfigHolder):

    def __init__(self, account_idx: Optional[int] = None):
        super().__init__(AppDescriptionEnum.WORLD_PATROL.value.id,
                         account_idx=account_idx)

    @property
    def team_num(self) -> int:
        return self.get('team_num', 0)

    @team_num.setter
    def team_num(self, new_value: int):
        self.update('team_num', new_value)

    @property
    def whitelist_id(self) -> str:
        return self.get('whitelist_id', '')

    @whitelist_id.setter
    def whitelist_id(self, new_value: str):
        self.update('whitelist_id', new_value)

    @property
    def technique_fight(self) -> bool:
        return self.get('technique_fight', False)

    @technique_fight.setter
    def technique_fight(self, new_value: bool):
        self.update('technique_fight', new_value)

    @property
    def technique_only(self) -> bool:
        """
        只使用秘技
        :return:
        """
        return self.get('technique_only', False)

    @technique_only.setter
    def technique_only(self, new_value: bool):
        self.update('technique_only', new_value)

    @property
    def max_consumable_cnt(self) -> bool:
        return self.get('max_consumable_cnt', 0)

    @max_consumable_cnt.setter
    def max_consumable_cnt(self, new_value: int):
        self.update('max_consumable_cnt', new_value)

    @property
    def radiant_feldspar_name(self) -> str:
        return self.get('radiant_feldspar_name', '晖长石号')

    @radiant_feldspar_name.setter
    def radiant_feldspar_name(self, new_value: str):
        self.update('radiant_feldspar_name', new_value)
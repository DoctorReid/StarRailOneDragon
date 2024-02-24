from typing import Optional

from basic.config import ConfigHolder
from sr.app.app_description import AppDescriptionEnum


class WorldPatrolConfig(ConfigHolder):

    def __init__(self, account_idx: Optional[int] = None):
        super().__init__(AppDescriptionEnum.WORLD_PATROL.value.id,
                         account_idx=account_idx,
                         sub_dir=['world_patrol'])

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

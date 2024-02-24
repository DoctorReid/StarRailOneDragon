from enum import Enum


class AppDescription:

    def __init__(self, cn: str, id: str):
        self.cn: str = cn
        self.id: str = id


class AppDescriptionEnum(Enum):
    WORLD_PATROL = AppDescription(cn='锄大地', id='world_patrol')
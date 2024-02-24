from enum import Enum


class AppDescription:

    def __init__(self, cn: str, id: str):
        self.cn: str = cn
        self.id: str = id


class AppDescriptionEnum(Enum):
    WORLD_PATROL = AppDescription(cn='锄大地', id='world_patrol')
    TRAILBLAZE_POWER = AppDescription(cn='开拓力', id='trailblaze_power')
    TREASURES_LIGHTWARD = AppDescription(cn='逐光捡金', id='treasures_lightward')

    ASSIGNMENTS = AppDescription(cn='委托', id='assignments')
    BUY_XIANZHOU_PARCEL = AppDescription(cn='过期邮包', id='buy_xianzhou_parcel')
    DAILY_TRAINING = AppDescription(cn='每日实训', id='daily_training')

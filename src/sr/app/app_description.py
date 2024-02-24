from enum import Enum


class AppDescription:

    def __init__(self, cn: str, id: str):
        self.cn: str = cn
        self.id: str = id


class AppDescriptionEnum(Enum):
    WORLD_PATROL = AppDescription(cn='锄大地', id='world_patrol')
    TRAILBLAZE_POWER = AppDescription(cn='开拓力', id='trailblaze_power')
    TREASURES_LIGHTWARD = AppDescription(cn='逐光捡金', id='treasures_lightward')
    ECHO_OF_WAR = AppDescription(cn='历战余响', id='echo_of_war')

    ASSIGNMENTS = AppDescription(cn='委托', id='assignments')
    BUY_XIANZHOU_PARCEL = AppDescription(cn='过期邮包', id='buy_xianzhou_parcel')
    DAILY_TRAINING = AppDescription(cn='每日实训', id='daily_training')
    EMAIL = AppDescription(cn='邮件', id='email')
    NAMELESS_HONOR = AppDescription(cn='无名勋礼', id='nameless_honor')
    SUPPORT_CHARACTER = AppDescription(cn='支援角色', id='support_character')


from typing import TypedDict, List, Optional


class AppDescription:

    def __init__(self, cn: str, id: str):
        self.cn: str = cn
        self.id: str = id


ASSIGNMENTS = AppDescription(cn='委托', id='assignments')
WORLD_PATROL = AppDescription(cn='锄大地', id='world_patrol')
EMAIL = AppDescription(cn='邮件', id='email')
SUPPORT_CHARACTER = AppDescription(cn='支援角色', id='support_character')
NAMELESS_HONOR = AppDescription(cn='无名勋礼', id='nameless_honor')
CLAIM_TRAINING = AppDescription(cn='实训奖励', id='claim_training')
BUY_XIANZHOU_PARCEL = AppDescription(cn='过期包裹', id='buy_xianzhou_parcel')

ROUTINE_APP_LIST: List[AppDescription] = [
    WORLD_PATROL,
    ASSIGNMENTS,
    EMAIL,
    SUPPORT_CHARACTER,
    NAMELESS_HONOR,
    CLAIM_TRAINING,
    BUY_XIANZHOU_PARCEL
]


def get_app_desc_by_id(app_id: str) -> Optional[AppDescription]:
    for app in ROUTINE_APP_LIST:
        if app.id == app_id:
            return app
    return None


class AppRunFrequency:

    def __init__(self, cn: str, id: str):
        self.cn: str = cn
        self.id: str = id


FREQUENCY_SKIP = AppRunFrequency(cn='跳过', id='skip')
FREQUENCY_EVERY_TIME = AppRunFrequency(cn='每次运行', id='every_time')
FREQUENCY_EVERY_DAY = AppRunFrequency(cn='每天一次', id='every_day')
FREQUENCY_EVERY_WEEK = AppRunFrequency(cn='每周一次', id='every_week')
FREQUENCY_EVERY_2_WEEK = AppRunFrequency(cn='两周一次', id='every_2_week')

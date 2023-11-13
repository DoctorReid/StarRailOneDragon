from typing import TypedDict, List, Optional


class AppDescription(TypedDict):
    cn: str
    id: str


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
        if app['id'] == app_id:
            return app
    return None

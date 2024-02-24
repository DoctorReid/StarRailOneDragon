from typing import List, Optional

from sr.app.app_description import AppDescription
from sr.app.app_run_record import AppRunRecord

ALL_APP_LIST: List[AppDescription] = [
]


def register_app(app_desc: AppDescription):
    """
    注册app 注册后才能在一条龙上看到
    :param app_desc:
    :return:
    """
    ALL_APP_LIST.append(app_desc)


def get_app_desc_by_id(app_id: str) -> Optional[AppDescription]:
    for app in ALL_APP_LIST:
        if app.id == app_id:
            return app
    return None

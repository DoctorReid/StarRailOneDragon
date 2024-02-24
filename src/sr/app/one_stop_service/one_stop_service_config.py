from typing import List, Optional

from basic.config import ConfigHolder
from sr.app.app_description import AppDescriptionEnum


class OneStopServiceConfig(ConfigHolder):

    def __init__(self, account_idx: Optional[int] = None):
        super().__init__('one_stop_service', account_idx=account_idx)

    def _init_after_read_file(self):
        current_list = self.order_app_id_list
        need_update: bool = False
        for app_enum in AppDescriptionEnum:
            app = app_enum.value
            if app.id not in current_list:
                current_list.append(app.id)
                need_update = True

        new_list = []
        for app_id in current_list:
            valid = False
            for app_enum in AppDescriptionEnum:
                app = app_enum.value
                if app_id == app.id:
                    valid = True
                    break
            if valid:
                new_list.append(app_id)
            else:
                need_update = True

        if need_update:
            self.order_app_id_list = new_list

    @property
    def order_app_id_list(self) -> List[str]:
        return self.get('app_order')

    @order_app_id_list.setter
    def order_app_id_list(self, new_list: List[str]):
        self.update('app_order', new_list)
        self.save()

    @property
    def run_app_id_list(self) -> List[str]:
        return self.get('app_run')

    @run_app_id_list.setter
    def run_app_id_list(self, new_list: List[str]):
        self.update('app_run', new_list)
        self.save()

    @property
    def schedule_hour_1(self):
        return self.get('schedule_hour_1', 'none')

    @schedule_hour_1.setter
    def schedule_hour_1(self, new_value: str):
        self.update('schedule_hour_1', new_value)

    @property
    def schedule_hour_2(self):
        return self.get('schedule_hour_2', 'none')

    @schedule_hour_2.setter
    def schedule_hour_2(self, new_value: str):
        self.update('schedule_hour_2', new_value)

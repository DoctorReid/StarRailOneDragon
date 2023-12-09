from typing import List

import flet as ft

from basic.i18_utils import gt
from basic.log_utils import log
from gui import components
from gui.components import SettingsListItem, SettingsList, SettingsListGroupTitle
from gui.sr_app_view import SrAppView
from sr.app import world_patrol
from sr.app.world_patrol import WorldPatrolWhitelist, load_all_whitelist_id, world_patrol_app
from sr.app.world_patrol.world_patrol_app import WorldPatrol
from sr.context import Context


class WorldPatrolRunView(SrAppView):

    def __init__(self, page: ft.Page, ctx: Context):
        super().__init__(page, ctx)

        self.whitelist_dropdown = ft.Dropdown(width=200)
        self.reset_btn = components.RectOutlinedButton('重置', on_click=self._on_click_reset)

        settings_list = components.SettingsList(
            controls=[
                components.SettingsListGroupTitle('设置'),
                components.SettingsListItem('路线名单', self.whitelist_dropdown),
                components.SettingsListItem('重置记录', self.reset_btn)
            ],
            width=400
        )

        self.existed_whitelist_id_list: List[str] = []

        self.diy_part.content = settings_list

    def handle_after_show(self):
        self.load_whitelist_id_list()
        self.update()

    def load_whitelist_id_list(self):
        self.existed_whitelist_id_list = load_all_whitelist_id()
        options = []
        options.append(ft.dropdown.Option(text=gt('无', 'ui'), key='none'))
        for i in range(len(self.existed_whitelist_id_list)):
            whitelist = WorldPatrolWhitelist(self.existed_whitelist_id_list[i])
            opt = ft.dropdown.Option(text=whitelist.name, key=whitelist.id)
            options.append(opt)
        self.whitelist_dropdown.options = options

    def run_app(self):
        whitelist: WorldPatrolWhitelist = None
        if self.whitelist_dropdown.value is not None and self.whitelist_dropdown.value != 'none':
            whitelist = WorldPatrolWhitelist(self.whitelist_dropdown.value)
        app = WorldPatrol(self.ctx, whitelist=whitelist)
        app.execute()

    def _on_click_reset(self, e):
        world_patrol.get_record().reset_record()
        log.info("运行记录已重置")


wprv: WorldPatrolRunView = None


def get(page: ft.Page, ctx: Context):
    global wprv
    if wprv is None:
        wprv = WorldPatrolRunView(page, ctx)
    return wprv

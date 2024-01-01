from typing import List

import flet as ft

from basic.i18_utils import gt
from basic.log_utils import log
from gui import components
from gui.components import SettingsListItem, SettingsList, SettingsListGroupTitle
from gui.sr_app_view import SrAppView
from sr.app import world_patrol
from sr.app.world_patrol import WorldPatrolWhitelist, load_all_whitelist_id, world_patrol_app, WorldPatrolConfig, \
    WorldPatrolRecord
from sr.app.world_patrol.world_patrol_app import WorldPatrol
from sr.context import Context


class WorldPatrolRunView(SrAppView):

    def __init__(self, page: ft.Page, ctx: Context):
        super().__init__(page, ctx)
        self.config: WorldPatrolConfig = world_patrol.get_config()
        self.record: WorldPatrolRecord = world_patrol.get_record()

        self.whitelist_dropdown = ft.Dropdown(width=200, on_change=self._on_whitelist_changed)
        self.reset_btn = components.RectOutlinedButton('重置', on_click=self._on_click_reset)

        settings_list = components.SettingsList(
            controls=[
                components.SettingsListGroupTitle('设置'),
                components.SettingsListItem('特定路线名单', self.whitelist_dropdown),
                components.SettingsListItem('重置记录', self.reset_btn)
            ],
            width=400
        )

        self.existed_whitelist_id_list: List[str] = []

        self.diy_part.content = settings_list

    def handle_after_show(self):
        self.load_whitelist_id_list()
        self._init_with_config()

    def load_whitelist_id_list(self):
        """
        加载名单列表
        :return:
        """
        self.existed_whitelist_id_list = load_all_whitelist_id()
        options = []
        options.append(ft.dropdown.Option(text=gt('无', 'ui'), key='none'))
        for i in range(len(self.existed_whitelist_id_list)):
            whitelist = WorldPatrolWhitelist(self.existed_whitelist_id_list[i])
            opt = ft.dropdown.Option(text=whitelist.name, key=whitelist.id)
            options.append(opt)
        self.whitelist_dropdown.options = options
        self.update()

    def _init_with_config(self):
        """
        加载配置
        :return:
        """
        self.whitelist_dropdown.value = self.config.whitelist_id
        self.update()

    def run_app(self):
        whitelist: WorldPatrolWhitelist = None
        if self.whitelist_dropdown.value is not None and self.whitelist_dropdown.value != 'none':
            whitelist = WorldPatrolWhitelist(self.whitelist_dropdown.value)
        world_patrol.get_record().check_and_update_status()
        app = WorldPatrol(self.sr_ctx, whitelist=whitelist)
        app.execute()

    def _on_click_reset(self, e):
        self.record.reset_record()
        log.info("运行记录已重置")

    def _on_whitelist_changed(self, e):
        self.config.whitelist_id = self.whitelist_dropdown.value


wprv: WorldPatrolRunView = None


def get(page: ft.Page, ctx: Context):
    global wprv
    if wprv is None:
        wprv = WorldPatrolRunView(page, ctx)
    return wprv

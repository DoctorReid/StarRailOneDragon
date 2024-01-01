from typing import Optional

import flet as ft

from basic.i18_utils import gt
from gui import components
from gui.components import SettingsListItem, SettingsList
from gui.sr_basic_view import SrBasicView
from sr.app import world_patrol
from sr.app.world_patrol import WorldPatrolWhitelist, load_all_whitelist_id
from sr.context import Context


class SettingsWorldPatrolView(SrBasicView, components.Card):

    def __init__(self, ctx: Context):
        self.ctx: Context = ctx
        self.config = world_patrol.get_config()

        plan_title = components.CardTitleText(gt('锄大地', 'ui'))

        self.team_num_dropdown = ft.Dropdown(options=[ft.dropdown.Option(text=str(i), key=str(i))for i in range(10)],
                                             on_change=self._on_team_num_changed)
        self.whitelist_dropdown = ft.Dropdown(on_change=self._on_whitelist_changed)
        self.plan_list = SettingsList(
            controls=[
                SettingsListItem('使用配队', self.team_num_dropdown),
                SettingsListItem('特定路线名单', self.whitelist_dropdown)
            ],
            width=400
        )

        components.Card.__init__(self, self.plan_list, plan_title, width=800)

    def handle_after_show(self):
        self._load_whitelist()
        self._init_by_config()

    def _load_whitelist(self):
        """
        读取名单列表
        :return:
        """
        whitelist_id_list = load_all_whitelist_id()
        options = [ft.dropdown.Option(text='无', key='none')]
        for whitelist_id in whitelist_id_list:
            whitelist = WorldPatrolWhitelist(whitelist_id)
            opt = ft.dropdown.Option(text=whitelist.name, key=whitelist.id)
            options.append(opt)
        self.whitelist_dropdown.options = options
        self.update()

    def _init_by_config(self):
        self.team_num_dropdown.value = str(self.config.team_num)
        self.whitelist_dropdown.value = self.config.whitelist_id
        self.update()

    def _on_team_num_changed(self, e):
        """
        使用配队变更
        :param e:
        :return:
        """
        self.config.team_num = int(self.team_num_dropdown.value)

    def _on_whitelist_changed(self, e):
        """
        特定路线名单变更
        :param e:
        :return:
        """
        self.config.whitelist_id = self.whitelist_dropdown.value


_settings_world_patrol_view: Optional[SettingsWorldPatrolView] = None


def get(ctx: Context) -> SettingsWorldPatrolView:
    global _settings_world_patrol_view
    if _settings_world_patrol_view is None:
        _settings_world_patrol_view = SettingsWorldPatrolView(ctx)
    return _settings_world_patrol_view

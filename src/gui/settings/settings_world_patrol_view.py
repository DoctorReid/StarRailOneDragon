from typing import Optional, List

import flet as ft

from basic.i18_utils import gt
from gui import components
from gui.components import SettingsListItem, SettingsList
from gui.settings import gui_config
from gui.sr_basic_view import SrBasicView
from sr.app import world_patrol
from sr.context import Context


class SettingsWorldPatrolView(SrBasicView, components.Card):

    def __init__(self, ctx: Context):
        self.ctx: Context = ctx
        self.config = world_patrol.get_config()

        plan_title = components.CardTitleText(gt('挑战规划', 'ui'))

        self.team_num_dropdown = ft.Dropdown(options=[ft.dropdown.Option(text=str(i), key=str(i))for i in range(7)],
                                             on_change=self._on_team_num_changed)
        self.route_list_dropdown = ft.Dropdown()
        self.plan_list = SettingsList(
            controls=[
                SettingsListItem('使用配队', self.team_num_dropdown)
            ],
            width=400
        )

        components.Card.__init__(self, self.plan_list, plan_title, width=800)

    def handle_after_show(self):
        self._init_by_config()
        pass

    def _init_by_config(self):
        self.team_num_dropdown.value = str(self.config.team_num)
        self.update()

    def _on_team_num_changed(self, e):
        self.config.team_num = int(self.team_num_dropdown.value)


_settings_world_patrol_view: Optional[SettingsWorldPatrolView] = None


def get(ctx: Context) -> SettingsWorldPatrolView:
    global _settings_world_patrol_view
    if _settings_world_patrol_view is None:
        _settings_world_patrol_view = SettingsWorldPatrolView(ctx)
    return _settings_world_patrol_view

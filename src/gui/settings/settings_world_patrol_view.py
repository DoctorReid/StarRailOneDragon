from typing import Optional, List

import flet as ft

from basic.i18_utils import gt
from gui import components
from gui.settings import gui_config
from gui.sr_basic_view import SrBasicView
from sr.app import world_patrol
from sr.context import Context


class SettingsListItem(ft.Row):

    def __init__(self, label: str, value_component):
        super().__init__(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[ft.Text(label), value_component]
        )


class SettingsList(ft.ListView):

    def __init__(self,
                 controls: Optional[List[SettingsListItem]] = None,
                 width: Optional[int] = None):
        theme = gui_config.theme()
        container_list = []
        if controls is not None:
            for i in controls:
                container = ft.Container(
                    content=i,
                    border=ft.border.only(bottom=ft.border.BorderSide(1, theme['divider_color'])),
                    padding=10
                )
                container_list.append(container)
        super().__init__(
            controls=container_list,
            width=width
        )


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

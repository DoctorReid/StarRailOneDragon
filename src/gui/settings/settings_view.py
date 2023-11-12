import flet as ft

from basic.i18_utils import gt
from gui.settings import settings_basic_view, gui_config
from gui.settings.gui_config import ThemeColors
from sr.context import Context


class SettingsView:

    def __init__(self, page: ft.Page, ctx: Context):
        self.page = page
        self.ctx = ctx

        theme: ThemeColors = gui_config.theme()
        self.rail_part = ft.NavigationRail(
            bgcolor=theme['component_bg'],
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=400,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.icons.SETTINGS_INPUT_COMPONENT_OUTLINED,
                    selected_icon=ft.icons.SETTINGS_INPUT_COMPONENT_ROUNDED,
                    label=gt('基础', model='ui')
                ),
            ],
            on_change=self.on_rail_chosen
        )

        self.display_part = ft.Container(content=settings_basic_view.get(page, ctx).component,
                                         padding=20)

        self.component = ft.Row(controls=[
            self.rail_part,
            self.display_part
        ], spacing=0)

    def on_rail_chosen(self, e):
        if self.rail_part.selected_index == 0:
            self.display_part.content = settings_basic_view.get(self.page, self.ctx).component
        else:
            self.display_part.content = None
        self.display_part.update()


sv: SettingsView = None


def get(page: ft.Page, ctx: Context) -> SettingsView:
    global sv
    if sv is None:
        sv = SettingsView(page, ctx)
    return sv

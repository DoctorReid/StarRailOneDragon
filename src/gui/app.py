import threading

import flet as ft
import keyboard

from basic.i18_utils import gt, update_default_lang
from gui import log_view, calibrator_view, version, routine_view, one_stop_view, gui_const
from gui.settings import settings_view
from gui.world_patrol import world_patrol_view
from sr.config import game_config
from sr.config.game_config import GameConfig
from sr.context import get_context, Context


class StarRailAutoProxy:

    def __init__(self, page: ft.Page, ctx: Context):
        self.page: ft.Page = page
        self.ctx: Context = ctx

        page.title = gt('崩坏：星穹铁道 自动代理器', model='ui') + ' ' + version.get_current_version()
        page.padding = 0

        self.display_part = ft.Container(content=world_patrol_view.get(page, ctx).component, bgcolor='#F9F9F9')

        self.rail_part = ft.NavigationRail(
            bgcolor=gui_const.RAIL_BG_COLOR,
            selected_index=1,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=400,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.icons.RUN_CIRCLE_OUTLINED,
                    selected_icon=ft.icons.RUN_CIRCLE,
                    label=gt('一条龙', model='ui')
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.RUN_CIRCLE_OUTLINED,
                    selected_icon=ft.icons.RUN_CIRCLE,
                    label=gt('锄大地', model='ui')
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.TODAY_OUTLINED,
                    selected_icon=ft.icons.TODAY_ROUNDED,
                    label=gt('日常', model='ui')
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.ADD_LOCATION_ALT_OUTLINED,
                    selected_icon=ft.icons.ADD_LOCATION_ALT_ROUNDED,
                    label=gt('校准', model='ui')
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.SETTINGS_OUTLINED,
                    selected_icon=ft.icons.SETTINGS,
                    label=gt('设置', model='ui')
                ),
            ],
            on_change=self.on_rail_chosen
        )

        page.add(
            ft.Row([
                self.rail_part,
                ft.VerticalDivider(width=1),
                self.display_part,
                ft.VerticalDivider(width=1),
                log_view.get(page)
            ], expand=True, spacing=0)
        )

        keyboard.on_press(self.on_key_press)

    def on_rail_chosen(self, e):
        if self.rail_part.selected_index == 0:
            self.display_part.content = one_stop_view.get(self.page, self.ctx).component
        elif self.rail_part.selected_index == 1:
            self.display_part.content = world_patrol_view.get(self.page, self.ctx).component
        elif self.rail_part.selected_index == 2:
            self.display_part.content = routine_view.get(self.page, self.ctx).component
        elif self.rail_part.selected_index == 3:
            self.display_part.content = calibrator_view.get(self.page, self.ctx).component
        elif self.rail_part.selected_index == 4:
            self.display_part.content = settings_view.get(self.page, self.ctx).component
        else:
            self.display_part.content = None
        self.page.update()

    def on_key_press(self, event):
        """
        监听F9 判断能否开始某个功能
        :param event:
        :return:
        """
        k = event.name
        if k != 'f9':
            return
        if self.ctx.running != 0:
            return
        t = None
        if self.rail_part.selected_index == 1:
            t = threading.Thread(target=world_patrol_view.get(self.page, self.ctx).start, args=[None])
        elif self.rail_part.selected_index == 2:
            t = threading.Thread(target=calibrator_view.get(self.page, self.ctx).start, args=[None])
        if t is not None:
            t.start()


def run_app(page: ft.Page):
    gc: GameConfig = game_config.get()
    update_default_lang(gc.lang)

    ctx = get_context()
    StarRailAutoProxy(page, ctx)


if __name__ == '__main__':
    ft.app(target=run_app, name='StarRailAutoProxy')
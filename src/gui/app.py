import logging
import threading
from typing import Optional

import flet as ft
import keyboard

from basic import os_utils
from basic.i18_utils import gt, update_default_lang
from gui import log_view, calibrator_view, version, one_stop_view, scheduler
from gui.settings import gui_config, settings_basic_view, settings_trailblaze_power_view, settings_echo_of_war_view, \
    settings_world_patrol_view, settings_mys_view, settings_forgotten_hall_view
from gui.settings.gui_config import ThemeColors, GuiConfig
from gui.sr_basic_view import SrBasicView
from gui.world_patrol import world_patrol_run_view, world_patrol_draft_route_view, world_patrol_whitelist_view
from sr.config import game_config
from sr.config.game_config import GameConfig
from sr.context import get_context, Context


class StarRailAutoProxy:

    def __init__(self, page: ft.Page, ctx: Context):
        self.page: ft.Page = page
        self.ctx: Context = ctx

        ui_config = gui_config.get()
        page.theme_mode = ft.ThemeMode.LIGHT if ui_config.theme_usage == ft.ThemeMode.LIGHT.value else ft.ThemeMode.DARK
        page.title = gt('崩坏：星穹铁道 自动代理器', model='ui') + ' ' + version.get_current_version()
        page.padding = 0

        theme: ThemeColors = gui_config.theme()
        self.display_view: SrBasicView = one_stop_view.get(page, ctx)
        self.display_part = ft.Container(content=self.display_view, padding=10)

        self.app_rail = ft.NavigationRail(
            bgcolor=theme['component_bg'],
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=400,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.icons.AIRPORT_SHUTTLE_OUTLINED,
                    selected_icon=ft.icons.AIRPORT_SHUTTLE_ROUNDED,
                    label=gt('一条龙', model='ui')
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.RUN_CIRCLE_OUTLINED,
                    selected_icon=ft.icons.RUN_CIRCLE,
                    label=gt('锄大地', model='ui')
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

        self.world_patrol_rail = ft.NavigationRail(
            bgcolor=theme['component_bg'],
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=400,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.icons.PLAY_CIRCLE_OUTLINED,
                    selected_icon=ft.icons.PLAY_CIRCLE_ROUNDED,
                    label=gt('运行', model='ui')
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.DRAW_OUTLINED,
                    selected_icon=ft.icons.DRAW,
                    label=gt('路线绘制', model='ui')
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.PLAYLIST_ADD_CHECK_OUTLINED,
                    selected_icon=ft.icons.PLAYLIST_ADD_CHECK_CIRCLE_ROUNDED,
                    label=gt('白名单编辑', model='ui')
                ),
            ],
            on_change=self.on_rail_chosen
        )

        self.settings_rail = ft.NavigationRail(
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
                ft.NavigationRailDestination(
                    icon=ft.icons.RUN_CIRCLE_OUTLINED,
                    selected_icon=ft.icons.RUN_CIRCLE,
                    label=gt('锄大地', model='ui')
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.SCHEDULE_SEND_OUTLINED,
                    selected_icon=ft.icons.SCHEDULE_SEND,
                    label=gt('开拓力', model='ui')
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.SURROUND_SOUND_OUTLINED,
                    selected_icon=ft.icons.SURROUND_SOUND,
                    label=gt('历战回响', model='ui')
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.BOOKMARKS_OUTLINED,
                    selected_icon=ft.icons.BOOKMARKS,
                    label=gt('忘却之庭', model='ui')
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.PEOPLE_OUTLINED,
                    selected_icon=ft.icons.PEOPLE,
                    label=gt('米游社', model='ui')
                ),
            ],
            on_change=self.on_rail_chosen
        )

        self.secondary_rail = ft.Container()
        self.secondary_rail_divider = ft.VerticalDivider(width=1, visible=False)
        self.log_container = ft.Container(content=log_view.get(page, ctx), padding=10)

        page.bgcolor = theme['window_bg']
        page.add(ft.Row([
            self.app_rail,
            ft.VerticalDivider(width=1),
            self.secondary_rail,
            self.secondary_rail_divider,
            self.display_part,
            self.log_container
        ], expand=True, spacing=0))

        self.display_view.handle_after_show()
        keyboard.on_press(self.on_key_press)

    def on_rail_chosen(self, e):
        self.display_view.handle_after_hide()
        self.display_view = self._get_view_component()
        self.display_part.content = self.display_view
        self.secondary_rail.content = self._get_secondary_rail()
        self.secondary_rail_divider.visible = self.secondary_rail.content is not None
        self.log_container.visible = self._get_log_visible_by_rail()
        self.page.update()
        self.display_view.handle_after_show()

    def _get_log_visible_by_rail(self) -> bool:
        if self.app_rail.selected_index == 0:
            return True
        elif self.app_rail.selected_index == 1:  # 锄大地
            if self.world_patrol_rail.selected_index in [0, 1]:
                return True
        elif self.app_rail.selected_index == 2:  # 校准
            return True
        elif self.app_rail.selected_index == 3:
            if self.settings_rail.selected_index == 0:  # 设置 - 基础
                return True
        return False

    def _get_secondary_rail(self):
        if self.app_rail.selected_index == 0:
            return None
        elif self.app_rail.selected_index == 1:
            return self.world_patrol_rail
        elif self.app_rail.selected_index == 2:
            return None
        elif self.app_rail.selected_index == 3:
            return self.settings_rail
        else:
            return None

    def _get_view_component(self) -> Optional[SrBasicView]:
        if self.app_rail.selected_index == 0:
            return one_stop_view.get(self.page, self.ctx)
        elif self.app_rail.selected_index == 1:
            if self.world_patrol_rail.selected_index == 0:
                return world_patrol_run_view.get(self.page, self.ctx)
            if self.world_patrol_rail.selected_index == 1:
                return world_patrol_draft_route_view.get(self.page, self.ctx)
            if self.world_patrol_rail.selected_index == 2:
                return world_patrol_whitelist_view.get(self.page, self.ctx)
        elif self.app_rail.selected_index == 2:
            return calibrator_view.get(self.page, self.ctx)
        elif self.app_rail.selected_index == 3:
            if self.settings_rail.selected_index == 0:
                return settings_basic_view.get(self.page, self.ctx)
            elif self.settings_rail.selected_index == 1:
                return settings_world_patrol_view.get(self.ctx)
            elif self.settings_rail.selected_index == 2:
                return settings_trailblaze_power_view.get(self.ctx)
            elif self.settings_rail.selected_index == 3:
                return settings_echo_of_war_view.get(self.ctx)
            elif self.settings_rail.selected_index == 4:
                return settings_forgotten_hall_view.get(self.page, self.ctx)
            elif self.settings_rail.selected_index == 5:
                return settings_mys_view.get(self.page, self.ctx)

        return None

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
        if self.app_rail.selected_index == 0:
            t = threading.Thread(target=one_stop_view.get(self.ctx).on_click_start, args=[None])
        elif self.app_rail.selected_index == 1:
            if self.world_patrol_rail.selected_index == 0:
                t = threading.Thread(target=world_patrol_run_view.get(self.page, self.ctx).start, args=[None])
            elif self.world_patrol_rail.selected_index == 1:
                t = threading.Thread(target=world_patrol_draft_route_view.get(self.page, self.ctx).test_existed, args=[None])
        elif self.app_rail.selected_index == 2:
            t = threading.Thread(target=calibrator_view.get(self.page, self.ctx).start, args=[None])
        if t is not None:
            t.start()


def run_app(page: ft.Page):
    ui_config: GuiConfig = gui_config.get()
    ui_config.init_system_theme(page.platform_brightness.value)

    gc: GameConfig = game_config.get()
    update_default_lang(gc.lang)

    scheduler.start()

    ctx = get_context()
    StarRailAutoProxy(page, ctx)


if __name__ == '__main__':
    if os_utils.is_debug():
        logging.getLogger("flet_core").setLevel(logging.INFO)
    ft.app(target=run_app, name='StarRailAutoProxy')
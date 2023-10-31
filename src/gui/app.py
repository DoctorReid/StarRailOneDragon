import flet as ft
import keyboard

from basic.i18_utils import gt, update_default_lang
from gui import world_patrol_view, log_view, calibrator_view, world_patrol_draft_route_view, world_patrol_whitelist_view, settings_view
from sr.config import game_config
from sr.config.game_config import GameConfig
from sr.context import get_context, Context


class StarRailAutoProxy:

    def __init__(self, page: ft.Page, ctx: Context):
        self.page: ft.Page = page
        self.ctx: Context = ctx

        page.title = gt('崩坏：星穹铁道 自动代理器', model='ui') + ' v0.5.4'

        self.display_part = ft.Container(content=world_patrol_view.get(page, ctx).component)

        self.rail_part = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=400,
            group_alignment=-0.9,
            destinations=[
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
                    icon=ft.icons.DRAW_OUTLINED,
                    selected_icon=ft.icons.DRAW,
                    label=gt('锄地路线绘制', model='ui')
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.PLAYLIST_ADD_CHECK_OUTLINED,
                    selected_icon=ft.icons.PLAYLIST_ADD_CHECK_CIRCLE_ROUNDED,
                    label=gt('锄地路线白名单', model='ui')
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
            ], expand=True)
        )

        keyboard.on_press(self.on_key_press)

    def on_rail_chosen(self, e):
        if self.rail_part.selected_index == 0:
            self.display_part.content = world_patrol_view.get(self.page, self.ctx).component
        elif self.rail_part.selected_index == 1:
            self.display_part.content = calibrator_view.get(self.page, self.ctx).component
        elif self.rail_part.selected_index == 2:
            self.display_part.content = world_patrol_draft_route_view.get(self.page, self.ctx).component
        elif self.rail_part.selected_index == 3:
            self.display_part.content = world_patrol_whitelist_view.get(self.page, self.ctx).component
        elif self.rail_part.selected_index == 4:
            self.display_part.content = settings_view.get(self.page, self.ctx).component
        else:
            self.display_part.content = None
        self.display_part.update()

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
        if self.rail_part.selected_index == 0:
            world_patrol_view.get(self.page, self.ctx).start(None)
        elif self.rail_part.selected_index == 1:
            calibrator_view.get(self.page, self.ctx).start(None)
        elif self.rail_part.selected_index == 2:
            world_patrol_draft_route_view.get(self.page, self.ctx).test_existed(None)



def run_app(page: ft.Page):
    gc: GameConfig = game_config.get()
    update_default_lang(gc.lang)

    ctx = get_context()
    StarRailAutoProxy(page, ctx)


if __name__ == '__main__':
    ft.app(target=run_app)
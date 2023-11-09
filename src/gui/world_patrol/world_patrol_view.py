import flet as ft
import threading

from basic.i18_utils import gt
from gui.world_patrol import world_patrol_run_view, world_patrol_draft_route_view, world_patrol_whitelist_view
from sr.context import Context


class WorldPatrolView:

    def __init__(self, page: ft.Page, ctx: Context):
        self.page = page
        self.ctx = ctx

        self.rail_part = ft.NavigationRail(
            bgcolor="#F3F6FC",
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

        self.display_part = ft.Container(content=world_patrol_run_view.get(page, ctx).component,
                                         padding=20)
        self.component = ft.Row(controls=[
            self.rail_part,
            self.display_part
        ], spacing=0)

    def on_rail_chosen(self, e):
        if self.rail_part.selected_index == 0:
            self.display_part.content = world_patrol_run_view.get(self.page, self.ctx).component
        elif self.rail_part.selected_index == 1:
            self.display_part.content = world_patrol_draft_route_view.get(self.page, self.ctx).component
        elif self.rail_part.selected_index == 2:
            self.display_part.content = world_patrol_whitelist_view.get(self.page, self.ctx).component
        else:
            self.display_part.content = None
        self.display_part.update()

    def start(self):
        if self.ctx.running != 0:
            return
        t = None
        if self.rail_part.selected_index == 0:
            t = threading.Thread(target=world_patrol_run_view.get(self.page, self.ctx).start, args=[None])
        elif self.rail_part.selected_index == 1:
            t = threading.Thread(target=world_patrol_draft_route_view.get(self.page, self.ctx).test_existed, args=[None])
        if t is not None:
            t.start()


wpv: WorldPatrolView = None


def get(page: ft.Page, ctx: Context):
    global wpv
    if wpv is None:
        wpv = WorldPatrolView(page, ctx)
    return wpv

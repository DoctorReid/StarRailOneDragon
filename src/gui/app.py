import flet as ft

from basic.i18_utils import gt
from gui import world_patrol_view, log_view, calibrator_view, world_patrol_draft_route_view, world_patrol_whitelist_view, settings_view
from sr.context import get_context


def run_app(page: ft.Page):
    ctx = get_context()
    page.title = gt('崩坏：星穹铁道 自动代理器') + ' v0.4.0'

    display_part = ft.Container(content=world_patrol_view.get(page, ctx).component)

    def on_rail_chosen(e):
        if e.control.selected_index == 0:
            display_part.content = world_patrol_view.get(page, ctx).component
        elif e.control.selected_index == 1:
            display_part.content = calibrator_view.get(page, ctx).component
        elif e.control.selected_index == 2:
            display_part.content = world_patrol_draft_route_view.get(page, ctx).component
        elif e.control.selected_index == 3:
            display_part.content = world_patrol_whitelist_view.get(page, ctx).component
        elif e.control.selected_index == 4:
            display_part.content = settings_view.get(page, ctx).component
        else:
            display_part.content = None
        display_part.update()

    rail_part = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=400,
        group_alignment=-0.9,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.icons.RUN_CIRCLE_OUTLINED,
                selected_icon=ft.icons.RUN_CIRCLE,
                label=gt('锄大地')
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.ADD_LOCATION_ALT_OUTLINED,
                selected_icon=ft.icons.ADD_LOCATION_ALT_ROUNDED,
                label=gt('校准')
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.DRAW_OUTLINED,
                selected_icon=ft.icons.DRAW,
                label=gt('锄地路线绘制')
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.PLAYLIST_ADD_CHECK_OUTLINED,
                selected_icon=ft.icons.PLAYLIST_ADD_CHECK_CIRCLE_ROUNDED,
                label=gt('锄地路线白名单')
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.SETTINGS_OUTLINED,
                selected_icon=ft.icons.SETTINGS,
                label=gt('设置')
            ),
        ],
        on_change=on_rail_chosen
    )

    page.add(
        ft.Row([
            rail_part,
            ft.VerticalDivider(width=1),
            display_part,
            ft.VerticalDivider(width=1),
            log_view.get(page)
        ], expand=True)
    )


if __name__ == '__main__':
    ft.app(target=run_app)
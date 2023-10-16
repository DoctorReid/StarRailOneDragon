import flet as ft

import sr.constants.map
from basic.i18_utils import gt
from sr.context import Context


class WorldPatrolDraftRouteView:

    def __init__(self, page: ft.Page, ctx: Context):
        self.page = page
        self.ctx = ctx

        self.planet_dropdown = ft.Dropdown(
            width=200,
            options=[
                ft.dropdown.Option(text=gt(p.cn), key=p.id) for p in sr.constants.map.PLANET_LIST
            ],
        )
        self.region_dropdown = ft.Dropdown(width=200)
        self.tp_dropdown = ft.Dropdown(width=200)

        choose_row = ft.Row(
            spacing=10,
            controls=[self.planet_dropdown, self.region_dropdown, self.tp_dropdown]
        )

        self.component = None

gv: WorldPatrolDraftRouteView = None

def get() -> WorldPatrolDraftRouteView:
    pass
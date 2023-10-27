from typing import List

import flet as ft

from gui.sr_app_view import SrAppView
from sr.app import world_patrol
from sr.app.world_patrol import WorldPatrolWhitelist
from sr.context import Context


class WorldPatrolView(SrAppView):

    def __init__(self, page: ft.Page, ctx: Context):
        super().__init__(page, ctx)

        settings_text = ft.Text(value='设置')

        self.whitelist_dropdown = ft.Dropdown(label='路线白名单', width=200, height=70)
        self.existed_whitelist_id_list: List[str] = []
        self.load_whitelist_id_list()

        self.diy_part.content = ft.Column(spacing=5, controls=[
            ft.Container(content=settings_text),
            ft.Container(content=self.whitelist_dropdown),
        ])

    def load_whitelist_id_list(self):
        self.existed_whitelist_id_list = world_patrol.load_all_whitelist_id()
        options = []
        options.append(ft.dropdown.Option(text='无', key='none'))
        for i in range(len(self.existed_whitelist_id_list)):
            opt = ft.dropdown.Option(text=self.existed_whitelist_id_list[i], key=self.existed_whitelist_id_list[i])
            options.append(opt)
        self.whitelist_dropdown.options = options

    def run_app(self):
        whitelist: WorldPatrolWhitelist = None
        if self.whitelist_dropdown.value is not None and self.whitelist_dropdown.value != 'none':
            whitelist = WorldPatrolWhitelist(self.whitelist_dropdown.value)
        app = world_patrol.WorldPatrol(self.ctx, whitelist=whitelist)
        app.execute()


wpv: WorldPatrolView = None


def get(page: ft.Page, ctx: Context):
    global wpv
    if wpv is None:
        wpv = WorldPatrolView(page, ctx)
    return wpv

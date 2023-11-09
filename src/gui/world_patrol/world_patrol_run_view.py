from typing import List

import flet as ft

from basic.i18_utils import gt
from gui.sr_app_view import SrAppView
from sr.app.world_patrol import WorldPatrolWhitelist, load_all_whitelist_id
from sr.app.world_patrol.world_patrol_app import WorldPatrol
from sr.context import Context


class WorldPatrolRunView(SrAppView):

    def __init__(self, page: ft.Page, ctx: Context):
        super().__init__(page, ctx)

        settings_text = ft.Text(value=gt('设置', 'ui'))

        self.whitelist_dropdown = ft.Dropdown(label=gt('路线白名单', 'ui'), width=200, height=70)
        self.existed_whitelist_id_list: List[str] = []
        self.load_whitelist_id_list()

        self.diy_part.content = ft.Column(spacing=5, controls=[
            ft.Container(content=settings_text),
            ft.Container(content=self.whitelist_dropdown),
        ])

    def on_rail_chosen(self, e):
        pass

    def load_whitelist_id_list(self):
        self.existed_whitelist_id_list = load_all_whitelist_id()
        options = []
        options.append(ft.dropdown.Option(text=gt('无', 'ui'), key='none'))
        for i in range(len(self.existed_whitelist_id_list)):
            opt = ft.dropdown.Option(text=self.existed_whitelist_id_list[i], key=self.existed_whitelist_id_list[i])
            options.append(opt)
        self.whitelist_dropdown.options = options

    def run_app(self):
        whitelist: WorldPatrolWhitelist = None
        if self.whitelist_dropdown.value is not None and self.whitelist_dropdown.value != 'none':
            whitelist = WorldPatrolWhitelist(self.whitelist_dropdown.value)
        app = WorldPatrol(self.ctx, whitelist=whitelist)
        app.execute()


wprv: WorldPatrolRunView = None


def get(page: ft.Page, ctx: Context):
    global wprv
    if wprv is None:
        wprv = WorldPatrolRunView(page, ctx)
    return wprv

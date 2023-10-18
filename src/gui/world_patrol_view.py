import flet as ft

from gui.sr_app_view import SrAppView
from sr.app.world_patrol import WorldPatrol
from sr.context import Context


class WorldPatrolView(SrAppView):

    def __init__(self, page: ft.Page, ctx: Context):
        super().__init__(page, ctx)

    def run_app(self):
        app = WorldPatrol(self.ctx)
        app.execute()


wpv: WorldPatrolView = None


def get(page: ft.Page, ctx: Context):
    global wpv
    if wpv is None:
        wpv = WorldPatrolView(page, ctx)
    return wpv

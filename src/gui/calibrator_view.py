import flet as ft

from gui.sr_app_view import SrAppView
from sr.app.calibrator import Calibrator
from sr.context import Context


class CalibratorView(SrAppView):

    def __init__(self, page: ft.Page, ctx: Context):
        super().__init__(page, ctx)

    def run_app(self):
        app = Calibrator(self.ctx)
        app.execute()


gv: CalibratorView = None


def get(page: ft.Page, ctx: Context):
    global gv
    if gv is None:
        gv = CalibratorView(page, ctx)
    return gv

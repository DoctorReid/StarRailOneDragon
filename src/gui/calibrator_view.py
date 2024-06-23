from typing import Optional

import flet as ft

from gui.sr_app_view import SrAppView
from sr.app.calibrator import Calibrator
from sr.context.context import Context


class CalibratorView(SrAppView):

    def __init__(self, page: ft.Page, ctx: Context):
        SrAppView.__init__(self, page, ctx)

    def run_app(self):
        app = Calibrator(self.sr_ctx)
        app.execute()


_calibrator_view: Optional[CalibratorView] = None


def get(page: ft.Page, ctx: Context) -> CalibratorView:
    global _calibrator_view
    if _calibrator_view is None:
        _calibrator_view = CalibratorView(page, ctx)
    return _calibrator_view

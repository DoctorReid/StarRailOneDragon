from typing import Optional

import flet as ft
import keyboard

from basic.i18_utils import gt
from basic.log_utils import log
from gui import components
from gui.sr_basic_view import SrBasicView
from sr.context import Context
from sr.operation.unit.rogue import UNI_NUM_CN


class SimUniDraftRouteView(components.Card, SrBasicView):

    def __init__(self, page: ft.Page, ctx: Context):
        SrBasicView.__init__(self, page, ctx)

        self.keyboard_hook = None

        num_dropdown = ft.Dropdown(
            label=gt('模拟宇宙', 'ui'),
            options=[
                ft.dropdown.Option(key=str(num), text=gt('第%s宇宙' % cn, 'ui')) for num, cn in UNI_NUM_CN.items()
            ],
        )

    def handle_after_show(self):
        self.keyboard_hook = keyboard.on_press(self._on_key_press)
        pass

    def handle_after_hide(self):
        keyboard.unhook(self.keyboard_hook)

    def _on_key_press(self, event):
        k = event.name
        log.info('模拟宇宙 路线绘制 触发按键 %s', k)


_sim_uni_draft_route_view: Optional[SimUniDraftRouteView] = None


def get(page: ft.Page, ctx: Context) -> SimUniDraftRouteView:
    global _sim_uni_draft_route_view
    if _sim_uni_draft_route_view is None:
        _sim_uni_draft_route_view = SimUniDraftRouteView(page, ctx)

    return _sim_uni_draft_route_view

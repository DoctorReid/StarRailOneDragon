import logging

import flet as ft

from basic import os_utils
from basic.log_utils import log
from gui import components
from gui.sr_basic_view import SrBasicView
from sr.context import Context


class GuiHandler(logging.Handler):
    def __init__(self, sp: ft.Page, list_view: ft.ListView):
        super().__init__()
        self.list_view = list_view
        self.sp = sp
        self.setLevel(logging.DEBUG if os_utils.is_debug() else logging.INFO)

    def emit(self, record):
        if self.list_view.page is not None:
            msg = self.format(record)
            self.list_view.controls.append(ft.Text(msg, size=10))
            if len(self.list_view.controls) > 50:  # 日志限制条数
                self.list_view.controls.pop(0)
            self.list_view.update()


class LogView(components.Card, SrBasicView):

    def __init__(self, page: ft.Page, ctx: Context):
        self.page: ft.Page = page
        self.ctx: Context = ctx

        log_list = ft.ListView(spacing=10, auto_scroll=True)
        log.addHandler(GuiHandler(page, list_view=log_list))

        title = components.CardTitleText('日志记录')

        components.Card.__init__(self, log_list, title=title, width=300)


log_view: LogView = None


def get(page: ft.Page, ctx: Context) -> LogView:
    global log_view
    if log_view is None:
        log_view = LogView(page, ctx)
    return log_view

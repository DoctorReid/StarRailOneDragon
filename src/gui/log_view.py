import logging

import flet as ft

from basic.log_utils import log


class GuiHandler(logging.Handler):
    def __init__(self, sp: ft.Page, list_view: ft.ListView):
        super().__init__()
        self.list_view = list_view
        self.sp = sp

    def emit(self, record):
        if self.list_view.page is not None:
            msg = self.format(record)
            self.list_view.controls.append(ft.Text(msg, size=10))
            if len(self.list_view.controls) > 1000:  # 日志限制条数
                self.list_view.controls.pop(0)
            self.list_view.update()


def get(sp: ft.Page):
    log_list = ft.ListView(expand=1, spacing=10, padding=20, auto_scroll=True)
    log.addHandler(GuiHandler(sp, list_view=log_list))

    log_view = ft.Container(padding=5, content=log_list)
    return log_view

import flet as ft

from basic.i18_utils import gt
from sr.context import Context


class OneStopView:

    def __init__(self, page: ft.Page, ctx: Context):
        self.page = page
        self.ctx = ctx

        info_text_width = 200
        info_text_spacing = 50
        self.info_update_time = ft.Text(value=gt('数据更新时间: 2023-11-09 00:00:00', 'ui'))
        self.power = ft.Text(value='开拓力: 240/240', width=info_text_width)
        self.training = ft.Text(value='实训: 500/500', width=info_text_width)
        self.echo = ft.Text(value='历战回响: 3/3', width=info_text_width)
        self.hall = ft.Text(value='忘却之庭: 30/30', width=info_text_width)
        self.sim = ft.Text(value='模拟宇宙: 14000/14000 34次', width=info_text_width * 2 + info_text_spacing)
        info_row_1 = ft.Row(controls=[self.power, self.training], spacing=info_text_spacing)
        info_row_2 = ft.Row(controls=[self.echo, self.hall], spacing=info_text_spacing)
        info_row_3 = ft.Row(controls=[self.sim])
        character_info_part = ft.Column(controls=[
            self.info_update_time,
            info_row_1,
            info_row_2,
            info_row_3
        ])

        self.component = ft.Container(content=character_info_part, padding=5)


osv: OneStopView = None


def get(page: ft.Page, ctx: Context):
    global osv
    if osv is None:
        osv = OneStopView(page, ctx)
    return osv

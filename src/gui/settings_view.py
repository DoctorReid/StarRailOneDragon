import flet as ft
from flet_core import CrossAxisAlignment

from basic.i18_utils import gt
from basic.log_utils import log
from sr import constants
from sr.config import game_config
from sr.config.game_config import GameConfig
from sr.context import Context


class SettingsView:

    def __init__(self, page: ft.Page, ctx: Context):
        self.page = page
        self.ctx = ctx

        self.save_btn = ft.ElevatedButton(text=gt("保存"), on_click=self.save_config)
        self.server_region = ft.Dropdown(
            label=gt("区服"), width=200,
            options=[
                ft.dropdown.Option(text=r, key=r) for r in constants.SERVER_TIME_OFFSET.keys()
            ],
        )

        self.component = ft.Column(
            spacing=20, horizontal_alignment=CrossAxisAlignment.CENTER, expand=True,
            controls=[
                ft.Container(content=self.server_region, padding=5),
                ft.Container(content=self.save_btn, padding=5),
            ])

        self.init_with_config()

    def init_with_config(self):
        """
        页面初始化加载已有配置
        :return:
        """
        gc: GameConfig = game_config.get()
        self.server_region.value = gc.server_region

    def save_config(self, e):
        config: GameConfig = game_config.get()
        config.update('server_region', self.server_region.value)
        config.write_config()
        log.info('保存成功')


sv: SettingsView = None


def get(page: ft.Page, ctx: Context) -> SettingsView:
    global sv
    if sv is None:
        sv = SettingsView(page, ctx)
    return sv

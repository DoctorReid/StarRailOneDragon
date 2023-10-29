import flet as ft
from flet_core import CrossAxisAlignment

from basic import i18_utils
from basic.i18_utils import gt
from basic.log_utils import log
from sr.config import game_config
from sr.config.game_config import GameConfig
from sr.const import game_config_const
from sr.context import Context


class SettingsView:

    def __init__(self, page: ft.Page, ctx: Context):
        self.page = page
        self.ctx = ctx

        self.server_region = ft.Dropdown(
            label=gt("区服", model='ui'), width=200,
            options=[
                ft.dropdown.Option(text=r, key=r) for r in game_config_const.SERVER_TIME_OFFSET.keys()
            ],
            on_change=self.on_server_region_changed
        )
        self.run_mode_dropdown = ft.Dropdown(
            label=gt("疾跑设置", model='ui'), width=200,
            options=[
                ft.dropdown.Option(text=gt(k, 'ui'), key=v) for k, v in game_config_const.RUN_MODE.items()
            ],
            on_change=self.on_run_mode_changed
        )
        self.lang_dropdown = ft.Dropdown(
            label=gt("语言", model='ui'), width=200,
            options=[
                ft.dropdown.Option(text=k, key=v) for k, v in game_config_const.LANG_OPTS.items()
            ],
            on_change=self.on_lang_changed
        )

        self.save_btn = ft.ElevatedButton(text=gt("保存", model='ui'), on_click=self.save_config)

        self.component = ft.Column(
            spacing=20, horizontal_alignment=CrossAxisAlignment.CENTER, expand=True,
            controls=[
                ft.Container(content=self.server_region, padding=5),
                ft.Container(content=self.run_mode_dropdown, padding=5),
                ft.Container(content=self.lang_dropdown, padding=5),
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
        self.run_mode_dropdown.value = gc.run_mode
        self.lang_dropdown.value = gc.lang

    def on_server_region_changed(self, e):
        gc: GameConfig = game_config.get()
        gc.set_server_region(self.server_region.value)

    def on_run_mode_changed(self, e):
        gc: GameConfig = game_config.get()
        gc.set_run_mode(int(self.run_mode_dropdown.value))

    def on_lang_changed(self, e):
        gc: GameConfig = game_config.get()
        gc.set_lang(self.lang_dropdown.value)
        i18_utils.update_default_lang(self.lang_dropdown.value)

    def save_config(self, e):
        gc: GameConfig = game_config.get()
        gc.write_config()
        log.info('保存成功')


sv: SettingsView = None


def get(page: ft.Page, ctx: Context) -> SettingsView:
    global sv
    if sv is None:
        sv = SettingsView(page, ctx)
    return sv

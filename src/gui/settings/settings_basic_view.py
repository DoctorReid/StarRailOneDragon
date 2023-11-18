import flet as ft
from flet_core import CrossAxisAlignment

from basic import i18_utils, os_utils
from basic.i18_utils import gt
from basic.log_utils import log
from gui import version, snack_bar, components
from gui.settings import gui_config
from gui.settings.gui_config import GuiConfig
from gui.sr_basic_view import SrBasicView
from sr.config import game_config
from sr.config.game_config import GameConfig
from sr.const import game_config_const
from sr.context import Context


class SettingsView(components.Card, SrBasicView):

    def __init__(self, page: ft.Page, ctx: Context):
        self.page = page
        self.ctx = ctx

        self.gui_config: GuiConfig = gui_config.get()

        self.server_region = ft.Dropdown(
            label=gt("区服", model='ui'), width=150,
            options=[
                ft.dropdown.Option(text=r, key=r) for r in game_config_const.SERVER_TIME_OFFSET.keys()
            ],
            on_change=self.on_server_region_changed
        )
        self.run_mode_dropdown = ft.Dropdown(
            label=gt("疾跑设置", model='ui'), width=150,
            options=[
                ft.dropdown.Option(text=gt(k, 'ui'), key=v) for k, v in game_config_const.RUN_MODE.items()
            ],
            on_change=self.on_run_mode_changed
        )
        self.lang_dropdown = ft.Dropdown(
            label=gt("语言", model='ui'), width=150,
            options=[
                ft.dropdown.Option(text=k, key=v) for k, v in game_config_const.LANG_OPTS.items()
            ],
            on_change=self.on_lang_changed
        )

        self.gui_theme_dropdown = ft.Dropdown(
            label=gt('界面主题', 'ui'), width=150,
            options=[ft.dropdown.Option(text=gt(i.cn, 'ui'), key=i.id) for i in gui_config.ALL_GUI_THEME_LIST],
            value=self.gui_config.theme,
            on_change=self._on_ui_theme_changed
        )
        basic_settings_row = ft.Row(controls=[
            self.server_region,
            self.run_mode_dropdown,
            self.lang_dropdown,
            self.gui_theme_dropdown
        ])

        self.game_path_pick_dialog = ft.FilePicker(on_result=self.on_game_path_pick)
        self.game_path_text = ft.Text(width=400, overflow=ft.TextOverflow.ELLIPSIS)
        self.page.overlay.append(self.game_path_pick_dialog)
        self.game_path_btn = ft.ElevatedButton(text=gt("游戏路径", model='ui'), on_click=self.show_game_path_pick)
        game_path_row = ft.Row(controls=[
            self.game_path_btn,
            self.game_path_text
        ])

        self.save_btn = ft.ElevatedButton(text=gt("保存", model='ui'), on_click=self.save_config)

        self.proxy_switch = ft.Switch(label=gt('启用代理', 'ui'), value=False, on_change=self.on_proxy_switch)
        self.proxy_input = ft.TextField(label=gt('代理地址', 'ui'), hint_text='host:port', width=150,
                                        value='http://127.0.0.1:8234', disabled=True)
        self.pre_release_switch = ft.Switch(label=gt('测试版', 'ui'), value=False, on_change=self.on_prerelease_switch)
        self.check_update_btn = ft.ElevatedButton(text=gt("检查更新", model='ui'), on_click=self.check_update)
        self.update_btn = ft.ElevatedButton(text=gt("更新", model='ui'), on_click=self.do_update, visible=False)

        proxy_host_row = ft.Row(controls=[
            self.proxy_input,
            self.proxy_switch
        ], spacing=5)
        update_btn_row = ft.Row(controls=[
            self.check_update_btn,
            self.update_btn,
            self.pre_release_switch
        ], spacing=5)

        content = ft.Column(
            spacing=20, horizontal_alignment=CrossAxisAlignment.CENTER, expand=True,
            controls=[
                ft.Container(content=basic_settings_row, padding=5),
                ft.Container(content=game_path_row, padding=5),
                ft.Container(content=self.save_btn, padding=5),
                ft.Container(content=proxy_host_row, padding=5),
                ft.Container(content=update_btn_row, padding=5),
            ])

        components.Card.__init__(self, content)

    def handle_after_show(self):
        self._init_with_config()

    def _init_with_config(self):
        """
        页面初始化加载已有配置
        :return:
        """
        gc: GameConfig = game_config.get()
        self.server_region.value = gc.server_region
        self.run_mode_dropdown.value = gc.run_mode
        self.lang_dropdown.value = gc.lang
        self.game_path_text.value = gc.game_path
        self.update()

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
        gc.save()
        log.info('保存成功')

    def on_proxy_switch(self, e):
        self.proxy_input.disabled = not self.proxy_switch.value
        self.page.update()

    def on_prerelease_switch(self, e):
        if self.pre_release_switch.value:
            msg: str = gt('测试版可能功能不稳定 如遇问题，可关闭后再次更新', 'ui')
            snack_bar.show_message(msg, self.page)
            log.info(msg)

    def check_update(self, e):
        version_result = version.check_new_version(proxy=None if self.proxy_input.disabled else self.proxy_input.value,
                                                   pre_release=self.pre_release_switch.value)
        if version_result == 2:
            msg: str = gt('检测更新请求失败', 'ui')
            snack_bar.show_message(msg, self.page)
            log.info(msg)
        elif version_result == 1:
            if os_utils.run_in_flet_exe():
                msg: str = gt('检测到新版本 再次点击进行更新 更新过程会自动关闭脚本 完成后请自动启动', 'ui')
                snack_bar.show_message(msg, self.page)
                log.info(msg)
                self.update_btn.visible = True
                self.check_update_btn.visible = False
                self.page.update()
            else:
                msg: str = gt('检测到新版本 请自行使用 git pull 更新', 'ui')
                snack_bar.show_message(msg, self.page)
                log.info(msg)
        else:
            msg: str = gt('已是最新版本', 'ui')
            snack_bar.show_message(msg, self.page)
            log.info(msg)

    def do_update(self, e):
        msg: str = gt('即将开始更新 更新过程会自动关闭脚本 完成后请自动启动', 'ui')
        snack_bar.show_message(msg, self.page)
        log.info(msg)
        self.update_btn.disabled = True
        self.page.update()
        try:
            version.do_update(proxy=None if self.proxy_input.disabled else self.proxy_input.value,
                              pre_release=self.pre_release_switch.value)
            self.page.window_close()
        except Exception:
            msg: str = gt('下载更新失败', 'ui')
            snack_bar.show_message(msg, self.page)
            log.error(msg, exc_info=True)
            self.update_btn.disabled = False
            self.page.update()

    def show_game_path_pick(self, e):
        self.game_path_pick_dialog.pick_files(allow_multiple=False, allowed_extensions=['exe'])

    def on_game_path_pick(self, e: ft.FilePickerResultEvent):
        if e.files is not None:
            self.game_path_text.value = e.files[0].path
            gc: GameConfig = game_config.get()
            gc.set_game_path(self.game_path_text.value)
            self.page.update()

    def _on_ui_theme_changed(self, e):
        self.gui_config.theme = self.gui_theme_dropdown.value


sv: SettingsView = None


def get(page: ft.Page, ctx: Context) -> SettingsView:
    global sv
    if sv is None:
        sv = SettingsView(page, ctx)
    return sv

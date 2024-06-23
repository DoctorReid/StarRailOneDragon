from typing import Optional

import flet as ft
import keyboard

from basic import i18_utils
from basic.i18_utils import gt
from gui import components
from gui.components import SettingsList, SettingsListItem, SettingsListGroupTitle
from gui.sr_basic_view import SrBasicView
from sr.const import game_config_const
from sr.context.context import Context


class SettingsGameConfigView(components.Card, SrBasicView):

    def __init__(self, page: ft.Page, ctx: Context):
        SrBasicView.__init__(self, page, ctx)

        self.server_region_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option(text=r, key=r) for r in game_config_const.SERVER_TIME_OFFSET.keys()],
            width=200, on_change=self.on_server_region_changed
        )

        self.lang_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option(text=k, key=v) for k, v in game_config_const.LANG_OPTS.items()],
            width=200, on_change=self.on_lang_changed
        )

        self.run_mode_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option(text=gt(k, 'ui'), key=v) for k, v in game_config_const.RUN_MODE.items()],
            width=200, on_change=self.on_run_mode_changed
        )
        self.use_quirky_snacks = ft.Checkbox(on_change=self._on_use_quirky_snacks)

        self.interact_btn = components.RectOutlinedButton(on_click=self._on_click_key_changed, data='key_interact')
        self.technique_btn = components.RectOutlinedButton(on_click=self._on_click_key_changed, data='key_technique')
        self.open_map_btn = components.RectOutlinedButton(on_click=self._on_click_key_changed, data='key_open_map')
        self.esc_btn = components.RectOutlinedButton(on_click=self._on_click_key_changed, data='key_esc')
        self.selected_key_btn: Optional[components.RectOutlinedButton] = None

        self.game_path_text = ft.Text(width=230, overflow=ft.TextOverflow.ELLIPSIS)
        self.game_path_btn = components.RectOutlinedButton(text='更改', on_click=self.show_game_path_pick)
        game_path_row = ft.Row(controls=[self.game_path_text, self.game_path_btn], width=300, spacing=0,
                               alignment=ft.MainAxisAlignment.START)
        self.game_path_pick_dialog = ft.FilePicker(on_result=self.on_game_path_pick)
        self.flet_page.overlay.append(self.game_path_pick_dialog)

        self.account_input = ft.TextField(on_change=self._on_account_change)
        self.password_input = ft.TextField(on_change=self._on_password_change)

        settings_list = SettingsList(
            controls=[
                SettingsListGroupTitle('基础'),
                SettingsListItem('游戏路径', game_path_row),
                SettingsListItem('游戏区服', self.server_region_dropdown),
                SettingsListItem('语言', self.lang_dropdown),
                SettingsListGroupTitle('通用'),
                SettingsListItem('疾跑', self.run_mode_dropdown),
                SettingsListItem('只使用奇巧零食', self.use_quirky_snacks),
                SettingsListItem('交互', self.interact_btn),
                SettingsListItem('秘技', self.technique_btn),
                SettingsListItem('打开地图', self.open_map_btn),
                SettingsListItem('返回', self.esc_btn),
                SettingsListGroupTitle('自动登录'),
                SettingsListItem('账号', self.account_input),
                SettingsListItem('密码', self.password_input),
            ],
            width=400
        )

        components.Card.__init__(self, settings_list)
        keyboard.on_press(self._on_key_press)

    def handle_after_show(self):
        self._init_with_config()

    def _init_with_config(self):
        """
        页面初始化加载已有配置
        :return:
        """
        self.server_region_dropdown.value = self.sr_ctx.game_config.server_region
        self.run_mode_dropdown.value = self.sr_ctx.game_config.run_mode
        self.lang_dropdown.value = self.sr_ctx.game_config.lang
        self.game_path_text.value = self.sr_ctx.game_config.game_path

        self.account_input.value = self.sr_ctx.game_config.game_account
        self.password_input.value = self.sr_ctx.game_config.game_account_password

        self.use_quirky_snacks.value = self.sr_ctx.game_config.use_quirky_snacks
        self.interact_btn.text = self.sr_ctx.game_config.key_interact
        self.technique_btn.text = self.sr_ctx.game_config.key_technique
        self.open_map_btn.text = self.sr_ctx.game_config.key_open_map
        self.esc_btn.text = self.sr_ctx.game_config.key_esc

        self.update()

    def on_server_region_changed(self, e):
        self.sr_ctx.game_config.server_region = self.server_region_dropdown.value

    def on_run_mode_changed(self, e):
        self.sr_ctx.game_config.run_mode = int(self.run_mode_dropdown.value)

    def on_lang_changed(self, e):
        self.sr_ctx.game_config.lang = self.lang_dropdown.value
        i18_utils.update_default_lang(self.lang_dropdown.value)

    def show_game_path_pick(self, e):
        self.game_path_pick_dialog.pick_files(allow_multiple=False, allowed_extensions=['exe'])

    def on_game_path_pick(self, e: ft.FilePickerResultEvent):
        if e.files is not None:
            self.game_path_text.value = e.files[0].path
            self.sr_ctx.game_config.game_path = self.game_path_text.value
            self.update()

    def _on_click_key_changed(self, e):
        """
        更改按键
        :param e:
        :return:
        """
        self.selected_key_btn = e.control
        self.selected_key_btn.text = gt('请按键', 'ui')
        self.update()

    def _on_key_press(self, e):
        """
        更改按键
        :param e: 按键事件
        :return:
        """
        if self.selected_key_btn is None:
            return

        key = e.name
        self.selected_key_btn.text = key
        self.update()
        self.sr_ctx.game_config.update(self.selected_key_btn.data, key)

        self.selected_key_btn = None

    def _on_account_change(self, e):
        self.sr_ctx.game_config.game_account = self.account_input.value

    def _on_password_change(self, e):
        self.sr_ctx.game_config.game_account_password = self.password_input.value

    def _on_use_quirky_snacks(self, e):
        """
        使用奇巧零食
        :param e:
        :return:
        """
        self.sr_ctx.game_config.use_quirky_snacks = self.use_quirky_snacks.value


_settings_game_config_view: Optional[SettingsGameConfigView] = None


def get(page: ft.Page, ctx: Context) -> SettingsGameConfigView:
    global _settings_game_config_view
    if _settings_game_config_view is None:
        _settings_game_config_view = SettingsGameConfigView(page, ctx)
    return _settings_game_config_view

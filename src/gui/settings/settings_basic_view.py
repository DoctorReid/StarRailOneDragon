from typing import Optional

import flet as ft
import keyboard
from flet_core import CrossAxisAlignment

from basic import i18_utils, os_utils
from basic.i18_utils import gt
from basic.log_utils import log
from gui import version, snack_bar, components
from gui.components import SettingsList, SettingsListItem, SettingsListGroupTitle
from gui.settings import gui_config
from gui.settings.gui_config import GuiConfig
from gui.sr_basic_view import SrBasicView
from sr.config import game_config
from sr.config.game_config import GameConfig
from sr.const import game_config_const
from sr.context import Context


class SettingsView(components.Card, SrBasicView):

    def __init__(self, page: ft.Page, ctx: Context):
        SrBasicView.__init__(self, page, ctx)

        self.gui_config: GuiConfig = gui_config.get()
        self.gui_theme_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option(text=gt(i.cn, 'ui'), key=i.id) for i in gui_config.ALL_GUI_THEME_LIST],
            value=self.gui_config.theme,
            width=200, on_change=self._on_ui_theme_changed
        )

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

        self.game_config: GameConfig = game_config.get()
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

        self.check_update_btn = components.RectOutlinedButton(text='检查更新', on_click=self.check_update)
        self.update_btn = components.RectOutlinedButton(text='更新', on_click=self.do_update, visible=False)
        self.pre_release_switch = ft.Switch(value=False, on_change=self.on_prerelease_switch)
        self.proxy_type_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option(text=gt(i.cn, 'ui'), key=i.id) for i in game_config_const.PROXY_TYPE_LIST
            ],
            width=150, on_change=self._on_proxy_type_changed
        )
        self.personal_proxy_input = ft.TextField(hint_text='host:port', width=150,
                                                 value='http://127.0.0.1:8234', disabled=True,
                                                 on_change=self._on_personal_proxy_changed)

        settings_list = SettingsList(
            controls=[
                SettingsListGroupTitle('基础'),
                SettingsListItem('界面主题', self.gui_theme_dropdown),
                SettingsListItem('游戏路径', game_path_row),
                SettingsListItem('游戏区服', self.server_region_dropdown),
                SettingsListItem('语言', self.lang_dropdown),
                SettingsListItem('疾跑', self.run_mode_dropdown),
                SettingsListGroupTitle('按键'),
                SettingsListItem('交互', self.interact_btn),
                SettingsListItem('秘技', self.technique_btn),
                SettingsListItem('打开地图', self.open_map_btn),
                SettingsListItem('返回', self.esc_btn),
                SettingsListGroupTitle('更新'),
                SettingsListItem('测试版本', self.pre_release_switch),
                SettingsListItem('代理类型', self.proxy_type_dropdown),
                SettingsListItem('代理地址', self.personal_proxy_input),
                SettingsListItem('检查更新', ft.Row(controls=[self.check_update_btn, self.update_btn])),
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
        self.server_region_dropdown.value = self.game_config.server_region
        self.run_mode_dropdown.value = self.game_config.run_mode
        self.lang_dropdown.value = self.game_config.lang
        self.game_path_text.value = self.game_config.game_path

        self.interact_btn.text = self.game_config.key_interact
        self.technique_btn.text = self.game_config.key_technique
        self.open_map_btn.text = self.game_config.key_open_map
        self.esc_btn.text = self.game_config.key_esc

        self.proxy_type_dropdown.value = self.game_config.proxy_type
        self.personal_proxy_input.value = self.game_config.personal_proxy
        self._update_proxy_part_display()

        self.update()

    def on_server_region_changed(self, e):
        self.game_config.server_region = self.server_region_dropdown.value

    def on_run_mode_changed(self, e):
        self.game_config.run_mode = int(self.run_mode_dropdown.value)

    def on_lang_changed(self, e):
        self.game_config.lang = self.lang_dropdown.value
        i18_utils.update_default_lang(self.lang_dropdown.value)

    def on_prerelease_switch(self, e):
        if self.pre_release_switch.value:
            msg: str = gt('测试版可能功能不稳定 如遇问题，可关闭后再次更新', 'ui')
            snack_bar.show_message(msg, self.flet_page)
            log.info(msg)

    def check_update(self, e):
        version_result = version.check_new_version(proxy=self.game_config.proxy_address,
                                                   pre_release=self.pre_release_switch.value)
        if version_result == 2:
            msg: str = gt('检测更新请求失败', 'ui')
            snack_bar.show_message(msg, self.flet_page)
            log.info(msg)
        elif version_result == 1:
            if os_utils.run_in_flet_exe():
                msg: str = gt('检测到新版本 再次点击进行更新 更新过程会自动关闭脚本 完成后请自动启动', 'ui')
                snack_bar.show_message(msg, self.flet_page)
                log.info(msg)
                self.update_btn.visible = True
                self.check_update_btn.visible = False
                self.update()
            else:
                msg: str = gt('检测到新版本 请自行使用 git pull 更新', 'ui')
                snack_bar.show_message(msg, self.flet_page)
                log.info(msg)
        else:
            msg: str = gt('已是最新版本', 'ui')
            snack_bar.show_message(msg, self.flet_page)
            log.info(msg)

    def do_update(self, e):
        msg: str = gt('即将开始更新 更新过程会自动关闭脚本 完成后请自动启动', 'ui')
        snack_bar.show_message(msg, self.flet_page)
        log.info(msg)
        self.update_btn.disabled = True
        self.update()
        try:
            version.do_update(proxy=self.game_config.proxy_address,
                              pre_release=self.pre_release_switch.value)
            self.flet_page.window_close()
        except Exception:
            msg: str = gt('下载更新失败', 'ui')
            snack_bar.show_message(msg, self.flet_page)
            log.error(msg, exc_info=True)
            self.update_btn.disabled = False
            self.update()

    def show_game_path_pick(self, e):
        self.game_path_pick_dialog.pick_files(allow_multiple=False, allowed_extensions=['exe'])

    def on_game_path_pick(self, e: ft.FilePickerResultEvent):
        if e.files is not None:
            self.game_path_text.value = e.files[0].path
            self.game_config.game_path = self.game_path_text.value
            self.update()

    def _on_ui_theme_changed(self, e):
        self.gui_config.theme = self.gui_theme_dropdown.value

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
        self.game_config.update(self.selected_key_btn.data, key)

        self.selected_key_btn = None

    def _update_proxy_part_display(self):
        """
        更新代理部分的显示
        :return:
        """
        self.personal_proxy_input.disabled = self.proxy_type_dropdown.value != 'personal'
        self.update()

    def _on_proxy_type_changed(self, e):
        """
        更改代理类型
        :param e:
        :return:
        """
        self.game_config.proxy_type = self.proxy_type_dropdown.value
        self._update_proxy_part_display()

    def _on_personal_proxy_changed(self, e):
        self.game_config.personal_proxy = self.personal_proxy_input.value


sv: SettingsView = None


def get(page: ft.Page, ctx: Context) -> SettingsView:
    global sv
    if sv is None:
        sv = SettingsView(page, ctx)
    return sv

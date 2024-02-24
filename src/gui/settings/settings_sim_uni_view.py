import re
from typing import Optional

import flet as ft

from basic.i18_utils import gt
from gui.components import Card, SettingsList, SettingsListItem, SettingsListGroupTitle
from gui.settings import gui_config
from gui.settings.gui_config import ThemeColors
from gui.sr_basic_view import SrBasicView
from sr.context import Context
from sr.sim_uni.sim_uni_const import SimUniWorldEnum


class SettingsSimUniView(ft.Row, SrBasicView):

    def __init__(self, page: ft.Page, ctx: Context):
        SrBasicView.__init__(self, page, ctx)
        theme: ThemeColors = gui_config.theme()

        self.weekly_uni_num = ft.Dropdown(
            options=[ft.dropdown.Option(key=world.name, text=gt(world.value.name, 'ui')) for world in SimUniWorldEnum],
            on_change=self._on_weekly_uni_num_changed
        )
        self.weekly_uni_diff = ft.Dropdown(
            options=[ft.dropdown.Option(key=str(i), text=str(i)) for i in range(1, 6)],
            on_change=self._on_weekly_uni_diff_changed
        )

        self.weekly_times = ft.TextField(on_change=self._on_weekly_times_changed)
        self.daily_times = ft.TextField(on_change=self._on_daily_times_changed)

        self.uni_03_dd = ft.Dropdown(data='sim_uni_03', on_change=self._on_sim_uni_challenge_changed)
        self.uni_04_dd = ft.Dropdown(data='sim_uni_04', on_change=self._on_sim_uni_challenge_changed)
        self.uni_05_dd = ft.Dropdown(data='sim_uni_05', on_change=self._on_sim_uni_challenge_changed)
        self.uni_06_dd = ft.Dropdown(data='sim_uni_06', on_change=self._on_sim_uni_challenge_changed)
        self.uni_07_dd = ft.Dropdown(data='sim_uni_07', on_change=self._on_sim_uni_challenge_changed)
        self.uni_08_dd = ft.Dropdown(data='sim_uni_08', on_change=self._on_sim_uni_challenge_changed)

        config_list = SettingsList(controls=[
            SettingsListGroupTitle(gt('模拟宇宙', 'ui')),
            SettingsListItem(gt('每周挑战', 'ui'), self.weekly_uni_num),
            SettingsListItem(gt('挑战难度', 'ui'), self.weekly_uni_diff),
            SettingsListItem(gt('每周次数', 'ui'), self.weekly_times),
            SettingsListItem(gt('每天次数', 'ui'), self.daily_times),
            SettingsListGroupTitle(gt('挑战设置', 'ui')),
            SettingsListItem(gt('第三宇宙', 'ui'), self.uni_03_dd),
            SettingsListItem(gt('第四宇宙', 'ui'), self.uni_04_dd),
            SettingsListItem(gt('第五宇宙', 'ui'), self.uni_05_dd),
            SettingsListItem(gt('第六宇宙', 'ui'), self.uni_06_dd),
            SettingsListItem(gt('第七宇宙', 'ui'), self.uni_07_dd),
            SettingsListItem(gt('第八宇宙', 'ui'), self.uni_08_dd),
        ], width=500)
        setting_card = Card(config_list)

        ft.Row.__init__(self, controls=[setting_card])

        self.config = self.sr_ctx.sim_uni_config

    def handle_after_show(self):
        self._load_existed_challenge_config_list()
        self._load_config()

    def _load_existed_challenge_config_list(self):
        all_config_list = self.sr_ctx.sim_uni_challenge_all_config.load_all_challenge_config()
        for uni_dd in [self.uni_03_dd, self.uni_04_dd, self.uni_05_dd, self.uni_06_dd, self.uni_07_dd, self.uni_08_dd]:
            uni_dd.options = [
                ft.dropdown.Option(key=config.uid, text=config.name) for config in all_config_list
            ]
            uni_dd.update()

    def _load_config(self):
        for uni_dd in [self.uni_03_dd, self.uni_04_dd, self.uni_05_dd, self.uni_06_dd, self.uni_07_dd, self.uni_08_dd]:
            uni_dd.value = self.config.get(uni_dd.data)
            uni_dd.update()

        self.weekly_uni_num.value = self.config.weekly_uni_num
        self.weekly_uni_num.update()

        self.weekly_uni_diff.value = str(self.config.weekly_uni_diff)
        self.weekly_uni_diff.update()

        self.weekly_times.value = str(self.config.weekly_times)
        self.weekly_times.update()

        self.daily_times.value = str(self.config.daily_times)
        self.daily_times.update()

    def _on_sim_uni_challenge_changed(self, e):
        """
        模拟宇宙挑战设置改变
        """
        self.config.update(e.control.data, e.control.value)

    def _on_weekly_uni_num_changed(self, e):
        """
        每周挑战宇宙设置
        """
        self.config.weekly_uni_num = self.weekly_uni_num.value

    def _on_weekly_uni_diff_changed(self, e):
        """
        每周挑战难度设置
        """
        self.config.weekly_uni_diff = int(self.weekly_uni_diff.value)

    def _on_weekly_times_changed(self, e):
        """
        每周挑战次数
        """
        text = re.sub(r'\D', '', self.weekly_times.value)
        if len(text) == 0:
            text = '0'
        if text != self.weekly_times.value:
            self.weekly_times.value = text
            self.weekly_times.update()
        self.config.weekly_times = int(text)

    def _on_daily_times_changed(self, e):
        """
        每天挑战次数
        """
        text = re.sub(r'\D', '', self.daily_times.value)
        if len(text) == 0:
            text = '0'
        if text != self.daily_times.value:
            self.daily_times.value = text
            self.daily_times.update()
        self.config.daily_times = int(text)


_settings_sim_uni_view: Optional[SettingsSimUniView] = None


def get(page: ft.Page, ctx: Context) -> SettingsSimUniView:
    global _settings_sim_uni_view
    if _settings_sim_uni_view is None:
        _settings_sim_uni_view = SettingsSimUniView(page, ctx)

    return _settings_sim_uni_view

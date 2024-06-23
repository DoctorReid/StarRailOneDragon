from typing import List, Optional

import flet as ft
import re

from basic.i18_utils import gt
from gui import components
from gui.sr_app_view import SrAppView
from sr.app.sim_uni.sim_uni_app import SimUniApp
from sr.context.context import Context
from sr.sim_uni.sim_uni_const import SimUniWorldEnum


class SimUniRunView(SrAppView):

    def __init__(self, page: ft.Page, ctx: Context):
        super().__init__(page, ctx)

        self.weekly_uni_num = ft.Dropdown(
            options=[ft.dropdown.Option(key=world.name, text=gt(world.value.name, 'ui')) for world in SimUniWorldEnum],
            on_change=self._on_weekly_uni_num_changed
        )
        self.weekly_uni_diff = ft.Dropdown(
            options=[ft.dropdown.Option(key=str(i), text='默认' if i == 0 else str(i)) for i in range(0, 6)],
            on_change=self._on_weekly_uni_diff_changed
        )

        self.weekly_times = ft.TextField(on_change=self._on_weekly_times_changed)
        self.daily_times = ft.TextField(on_change=self._on_daily_times_changed)

        settings_list = components.SettingsList(
            controls=[
                components.SettingsListItem(gt('每周挑战', 'ui'), self.weekly_uni_num),
                components.SettingsListItem(gt('挑战难度', 'ui'), self.weekly_uni_diff),
                components.SettingsListItem(gt('每周次数', 'ui'), self.weekly_times),
                components.SettingsListItem(gt('每天次数', 'ui'), self.daily_times),
            ],
            width=400
        )

        self.existed_whitelist_id_list: List[str] = []

        self.diy_part.content = settings_list

    def handle_after_show(self):
        self.weekly_uni_num.value = self.sr_ctx.sim_uni_config.weekly_uni_num
        self.weekly_uni_num.update()

        self.weekly_uni_diff.value = str(self.sr_ctx.sim_uni_config.weekly_uni_diff)
        self.weekly_uni_diff.update()

        self.weekly_times.value = str(self.sr_ctx.sim_uni_config.weekly_times)
        self.weekly_times.update()

        self.daily_times.value = str(self.sr_ctx.sim_uni_config.daily_times)
        self.daily_times.update()

    def _on_weekly_uni_num_changed(self, e):
        """
        每周挑战宇宙设置
        """
        self.sr_ctx.sim_uni_config.weekly_uni_num = self.weekly_uni_num.value

    def _on_weekly_uni_diff_changed(self, e):
        """
        每周挑战难度设置
        """
        self.sr_ctx.sim_uni_config.weekly_uni_diff = int(self.weekly_uni_diff.value)

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
        self.sr_ctx.sim_uni_config.weekly_times = int(text)

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
        self.sr_ctx.sim_uni_config.daily_times = int(text)

    def run_app(self):
        self.sr_ctx.sim_uni_run_record.check_and_update_status()
        app = SimUniApp(self.sr_ctx)
        app.execute()


_sim_uni_run_view: Optional[SimUniRunView] = None


def get(page: ft.Page, ctx: Context) -> SimUniRunView:
    global _sim_uni_run_view
    if _sim_uni_run_view is None:
        _sim_uni_run_view = SimUniRunView(page, ctx)
    return _sim_uni_run_view

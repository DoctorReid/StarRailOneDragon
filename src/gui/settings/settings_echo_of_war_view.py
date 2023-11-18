from typing import List, Optional

import flet as ft

from basic.i18_utils import gt
from gui import components
from gui.settings import gui_config
from gui.settings.gui_config import ThemeColors
from gui.sr_basic_view import SrBasicView
from sr.app.routine import echo_of_war
from sr.app.routine.echo_of_war import EchoOfWarConfig, EchoOfWarPlanItem
from sr.context import Context


class PlanListItem(ft.Row):

    def __init__(self, item: EchoOfWarPlanItem, on_value_changed=None):
        self.value: EchoOfWarPlanItem = item
        self.war_dropdown = ft.Dropdown(options=[ft.dropdown.Option(text=i.cn, key=str(i.unique_id)) for i in echo_of_war.WAR_LIST],
                                        label='挑战关卡', width=200, value=item['point_id'])
        self.team_num_dropdown = ft.Dropdown(options=[ft.dropdown.Option(text=str(i), key=str(i)) for i in range(1, 7)],
                                             label='使用配队', width=100, on_change=self._on_team_num_changed)
        self.plan_times_input = ft.TextField(label='计划次数', keyboard_type=ft.KeyboardType.NUMBER,
                                             width=100, on_change=self._on_plan_times_changed)
        self.run_times_input = ft.TextField(label='本轮完成', keyboard_type=ft.KeyboardType.NUMBER,
                                            width=100, on_change=self._on_run_times_changed)

        self.team_num_dropdown.value = self.value['team_num']
        self.plan_times_input.value = self.value['plan_times']
        self.run_times_input.value = self.value['run_times']
        self.value_changed_callback = on_value_changed

        super().__init__(controls=[self.war_dropdown, self.team_num_dropdown,
                                   self.run_times_input, self.plan_times_input])

    def _on_team_num_changed(self, e):
        self._update_value()
        if self.value_changed_callback is not None:
            self.value_changed_callback()

    def _on_plan_times_changed(self, e):
        if int(self.run_times_input.value) > int(self.plan_times_input.value):
            self.run_times_input.value = 0
            self.update()
        self._update_value()
        if self.value_changed_callback is not None:
            self.value_changed_callback()

    def _on_run_times_changed(self, e):
        if int(self.run_times_input.value) > int(self.plan_times_input.value):
            self.run_times_input.value = 0
            self.update()
        self._update_value()
        if self.value_changed_callback is not None:
            self.value_changed_callback()

    def _update_value(self):
        self.value['team_num'] = int(self.team_num_dropdown.value)
        self.value['plan_times'] = int(self.plan_times_input.value)
        self.value['run_times'] = int(self.run_times_input.value)

    def _update(self):
        if self.page is not None:
            self.update()


class PlanList(ft.ListView):

    def __init__(self):
        self.config: EchoOfWarConfig = echo_of_war.get_config()
        plan_item_list: List[EchoOfWarPlanItem] = self.config.plan_list

        super().__init__(controls=[self._list_view_item(i) for i in plan_item_list])

    def refresh_by_config(self):
        plan_item_list: List[EchoOfWarPlanItem] = self.config.plan_list
        self.controls = [self._list_view_item(i) for i in plan_item_list]
        self.update()

    def _list_view_item(self, plan_item: Optional[EchoOfWarPlanItem] = None) -> ft.Container:
        theme: ThemeColors = gui_config.theme()
        return ft.Container(
                content=PlanListItem(plan_item, on_value_changed=self._on_list_item_value_changed),
                border=ft.border.only(bottom=ft.border.BorderSide(1, theme['divider_color'])),
                padding=10
            )

    def _on_list_item_value_changed(self):
        plan_item_list: List[EchoOfWarPlanItem] = []
        for container in self.controls:
            item = container.content
            plan_item_list.append(item.value)
        self.config.plan_list = plan_item_list


class SettingsEchoOfWarView(SrBasicView, components.Card):

    def __init__(self, ctx: Context):
        self.ctx: Context = ctx
        self.config = echo_of_war.get_config()

        plan_title = components.CardTitleText(gt('挑战规划', 'ui'))

        self.plan_list = PlanList()

        components.Card.__init__(self, self.plan_list, plan_title, width=800)

    def handle_after_show(self):
        self.plan_list.refresh_by_config()


_settings_echo_of_war_view: Optional[SettingsEchoOfWarView] = None


def get(ctx: Context) -> SettingsEchoOfWarView:
    global _settings_echo_of_war_view
    if _settings_echo_of_war_view is None:
        _settings_echo_of_war_view = SettingsEchoOfWarView(ctx)
    return _settings_echo_of_war_view


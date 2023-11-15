from typing import Optional, List

import flet as ft

from basic.i18_utils import gt
from gui import components
from gui.settings import gui_config
from gui.settings.gui_config import ThemeColors
from gui.sr_basic_view import SrBasicView
from sr.app.routine import trailblaze_power
from sr.app.routine.trailblaze_power import TrailblazePowerConfig, TrailblazePowerPlanItem
from sr.operation.combine import use_trailblaze_power
from sr.operation.combine.use_trailblaze_power import TrailblazePowerPoint
from sr.context import Context


class PlanListItem(ft.Row):

    def __init__(self, item: Optional[TrailblazePowerPlanItem] = None,
                 on_value_changed=None,
                 on_click_up=None,
                 on_click_del=None):
        self.value: Optional[TrailblazePowerPlanItem] = item if item is not None else TrailblazePowerPlanItem(point_id=use_trailblaze_power.BUD_OF_MEMORIES.unique_id, plan_times=1, run_times=0)
        self.category_dropdown = ft.Dropdown(options=[ft.dropdown.Option(text=i, key=i) for i in
                                                      use_trailblaze_power.CATEGORY_LIST],
                                             label='类目', width=100, on_change=self._on_category_changed)
        self.tp_dropdown = ft.Dropdown(label='挑战关卡', width=200, on_change=self._on_tp_changed)
        self.team_num_dropdown = ft.Dropdown(options=[ft.dropdown.Option(text=str(i), key=str(i)) for i in range(1, 7)],
                                             label='使用配队', width=100, on_change=self._on_team_num_changed)
        self.plan_times_input = ft.TextField(label='计划次数', keyboard_type=ft.KeyboardType.NUMBER,
                                             width=100, on_change=self._on_plan_times_changed)
        self.run_times_input = ft.TextField(label='本轮完成', keyboard_type=ft.KeyboardType.NUMBER,
                                            width=100, on_change=self._on_run_times_changed)
        self.chosen_point: Optional[TrailblazePowerPoint] = use_trailblaze_power.get_point_by_unique_id(self.value['point_id'])

        self.category_dropdown.value = self.chosen_point.category
        self._update_tp_dropdown_list()
        self.tp_dropdown.value = self.chosen_point.unique_id
        self.team_num_dropdown.value = '1'
        self.plan_times_input.value = self.value['plan_times']
        self.run_times_input.value = self.value['run_times']
        self.value_changed_callback = on_value_changed

        self.up_app_btn = ft.IconButton(icon=ft.icons.ARROW_CIRCLE_UP_OUTLINED, data=id(self), on_click=on_click_up)
        self.del_btn = ft.IconButton(icon=ft.icons.DELETE_FOREVER_OUTLINED, data=id(self), on_click=on_click_del)

        super().__init__(controls=[self.category_dropdown, self.tp_dropdown, self.team_num_dropdown,
                                   self.run_times_input, self.plan_times_input,
                                   self.up_app_btn, self.del_btn])

    def _update_tp_dropdown_list(self):
        point_list: List[TrailblazePowerPoint] = use_trailblaze_power.CATEGORY_POINT_MAP.get(self.category_dropdown.value)
        if point_list is None:
            point_list = []
        self.tp_dropdown.options = [ft.dropdown.Option(text=i.display_name, key=i.unique_id) for i in point_list]
        self.tp_dropdown.value = self.tp_dropdown.options[0].key

    def _on_category_changed(self, e):
        self._update_tp_dropdown_list()
        self.plan_times_input.value = 1
        self.run_times_input.value = 0
        self._update_value()
        self._update()
        if self.value_changed_callback is not None:
            self.value_changed_callback()

    def _on_tp_changed(self, e):
        self.plan_times_input.value = 1
        self.run_times_input.value = 0
        self._update_value()
        self._update()
        if self.value_changed_callback is not None:
            self.value_changed_callback()

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
        self.value['point_id'] = self.tp_dropdown.value
        self.value['team_num'] = int(self.team_num_dropdown.value)
        self.value['plan_times'] = int(self.plan_times_input.value)
        self.value['run_times'] = int(self.run_times_input.value)

    def _update(self):
        if self.page is not None:
            self.update()


class PlanList(ft.ListView):

    def __init__(self):
        self.config: TrailblazePowerConfig = trailblaze_power.get_config()
        plan_item_list: List[TrailblazePowerPlanItem] = self.config.plan_list

        super().__init__(controls=[self._list_view_item(i) for i in plan_item_list])
        self.add_btn = ft.Container(components.RectOutlinedButton(text='+', on_click=self._on_add_click),
                                    margin=ft.margin.only(top=5))
        self.controls.append(self.add_btn)

    def refresh_by_config(self):
        plan_item_list: List[TrailblazePowerPlanItem] = self.config.plan_list
        self.controls = [self._list_view_item(i) for i in plan_item_list]
        self.controls.append(self.add_btn)
        self.update()

    def _list_view_item(self, plan_item: Optional[TrailblazePowerPlanItem] = None) -> ft.Container:
        theme: ThemeColors = gui_config.theme()
        return ft.Container(
                content=PlanListItem(plan_item, on_value_changed=self._on_list_item_value_changed,
                                     on_click_up=self._on_click_item_up,
                                     on_click_del=self._on_item_click_del),
                border=ft.border.only(bottom=ft.border.BorderSide(1, theme['divider_color'])),
                padding=10
            )

    def _on_add_click(self, e):
        self.controls.append(self._list_view_item())
        last = len(self.controls) - 1
        tmp = self.controls[last - 1]
        self.controls[last - 1] = self.controls[last]
        self.controls[last] = tmp
        self.update()
        self._on_list_item_value_changed()

    def _on_list_item_value_changed(self):
        plan_item_list: List[TrailblazePowerPlanItem] = []
        for container in self.controls:
            item = container.content
            if type(item) == PlanListItem:
                plan_item_list.append(item.value)
        self.config.plan_list = plan_item_list

    def _on_click_item_up(self, e):
        target_idx: int = -1
        for i in range(len(self.controls)):
            item = self.controls[i].content
            if type(item) == PlanListItem and id(item) == e.control.data:
                target_idx = i
                break

        if target_idx <= 0:
            return

        temp = self.controls[target_idx - 1]
        self.controls[target_idx - 1] = self.controls[target_idx]
        self.controls[target_idx] = temp

        self.update()
        self._on_list_item_value_changed()

    def _on_item_click_del(self, e):
        target_idx: int = -1
        for i in range(len(self.controls)):
            item = self.controls[i].content
            if type(item) == PlanListItem and id(item) == e.control.data:
                target_idx = i
                break

        if target_idx == - 1:
            return

        self.controls.pop(target_idx)
        self.update()
        self._on_list_item_value_changed()

    def _update_next_text(self):
        pass


class SettingsTrailblazePowerView(SrBasicView, components.Card):

    def __init__(self, ctx: Context):
        plan_title = components.CardTitleText(gt('体力规划', 'ui'))

        self.plan_list = PlanList()

        components.Card.__init__(self, self.plan_list, plan_title, width=800)

    def handle_after_show(self):
        self.plan_list.refresh_by_config()


_settings_trailblaze_power_view: Optional[SettingsTrailblazePowerView] = None


def get(ctx: Context) -> SettingsTrailblazePowerView:
    global _settings_trailblaze_power_view
    if _settings_trailblaze_power_view is None:
        _settings_trailblaze_power_view = SettingsTrailblazePowerView(ctx)
    return _settings_trailblaze_power_view

from typing import List, Optional, Callable

import flet as ft

from basic.i18_utils import gt
from gui import components
from gui.components.character_input import CharacterInput
from gui.settings import gui_config
from gui.settings.gui_config import ThemeColors
from gui.sr_basic_view import SrBasicView
from sr.app.routine import echo_of_war
from sr.app.routine.echo_of_war import EchoOfWarConfig, EchoOfWarPlanItem
from sr.const.character_const import CHARACTER_LIST
from sr.const.map_const import TransportPoint
from sr.context import Context
from sr.interastral_peace_guide.survival_index_mission import SurvivalIndexCategoryEnum, SurvivalIndexMission, \
    SurvivalIndexMissionEnum


class PlanListItem(ft.Row):

    def __init__(self, item: EchoOfWarPlanItem,
                 on_value_changed: Callable,
                 on_click_support: Callable):
        self.value: EchoOfWarPlanItem = item
        mission_list = SurvivalIndexMissionEnum.get_list_by_category(SurvivalIndexCategoryEnum.ECHO_OF_WAR.value)
        self.war_dropdown = ft.Dropdown(options=[
            ft.dropdown.Option(text=i.ui_cn, key=i.unique_id) for i in mission_list
        ],
                                        label='挑战关卡', width=200, value=item['mission_id'])
        self.team_num_dropdown = ft.Dropdown(options=[ft.dropdown.Option(text=str(i), key=str(i)) for i in range(1, 10)],
                                             label='使用配队', width=100, on_change=self._on_team_num_changed)
        self.support_dropdown = ft.Dropdown(label='支援', value='none', disabled=True, width=80,
                                            options=[ft.dropdown.Option(text='无', key='none')])
        for c in CHARACTER_LIST:
            self.support_dropdown.options.append(
                ft.dropdown.Option(text=gt(c.cn, 'ui'), key=c.id)
            )
        self.plan_times_input = ft.TextField(label='计划次数', keyboard_type=ft.KeyboardType.NUMBER,
                                             width=100, on_change=self._on_plan_times_changed)
        self.run_times_input = ft.TextField(label='本轮完成', keyboard_type=ft.KeyboardType.NUMBER,
                                            width=100, on_change=self._on_run_times_changed)

        self.team_num_dropdown.value = self.value['team_num']
        self.support_dropdown.value = self.value['support']
        self.plan_times_input.value = self.value['plan_times']
        self.run_times_input.value = self.value['run_times']
        self.value_changed_callback = on_value_changed

        super().__init__(controls=[self.war_dropdown, self.team_num_dropdown,
                                   ft.Container(content=self.support_dropdown, on_click=on_click_support, data=id(self)),
                                   self.run_times_input, self.plan_times_input])

    def _on_team_num_changed(self, e):
        self._update_value()

    def _on_plan_times_changed(self, e):
        if int(self.run_times_input.value) > int(self.plan_times_input.value):
            self.run_times_input.value = 0
            self.update()
        self._update_value()

    def _on_run_times_changed(self, e):
        if int(self.run_times_input.value) > int(self.plan_times_input.value):
            self.run_times_input.value = 0
            self.update()
        self._update_value()

    def _update_value(self):
        self.value['team_num'] = int(self.team_num_dropdown.value)
        self.value['support'] = self.support_dropdown.value
        self.value['plan_times'] = int(self.plan_times_input.value)
        self.value['run_times'] = int(self.run_times_input.value)

        if self.value_changed_callback is not None:
            self.value_changed_callback()

    def _update(self):
        if self.page is not None:
            self.update()

    def update_support(self, c_id: Optional[str]):
        """
        更新使用的支援角色
        :param c_id: 角色ID
        :return:
        """
        if c_id is None:
            c_id = 'none'
        if self.support_dropdown.value == c_id:
            return
        self.support_dropdown.value = c_id
        self._update()
        self._update_value()


class PlanList(ft.ListView):

    def __init__(self, on_click_support: Callable):
        self.config: EchoOfWarConfig = echo_of_war.get_config()
        plan_item_list: List[EchoOfWarPlanItem] = self.config.plan_list

        super().__init__(controls=[self._list_view_item(i) for i in plan_item_list])

        self.click_support_callback: Callable = on_click_support

    def refresh_by_config(self):
        plan_item_list: List[EchoOfWarPlanItem] = self.config.plan_list
        self.controls = [self._list_view_item(i) for i in plan_item_list]
        self.update()

    def _list_view_item(self, plan_item: Optional[EchoOfWarPlanItem] = None) -> ft.Container:
        theme: ThemeColors = gui_config.theme()
        return ft.Container(
                content=PlanListItem(plan_item,
                                     on_value_changed=self._on_list_item_value_changed,
                                     on_click_support=self._on_click_support),
                border=ft.border.only(bottom=ft.border.BorderSide(1, theme['divider_color'])),
                padding=10
            )

    def _on_list_item_value_changed(self):
        plan_item_list: List[EchoOfWarPlanItem] = []
        for container in self.controls:
            item = container.content
            plan_item_list.append(item.value)
        self.config.plan_list = plan_item_list

    def _on_click_support(self, e):
        target_idx = self._get_item_event_idx(e)
        if target_idx == - 1:
            return

        if self.click_support_callback is not None:
            self.click_support_callback(self.controls[target_idx].content)

    def _get_item_event_idx(self, e) -> int:
        """
        获取事件对应的行明细下标
        :param e: 事件
        :return: 下标
        """
        target_idx: int = -1
        for i in range(len(self.controls)):
            item = self.controls[i].content
            if type(item) == PlanListItem and id(item) == e.control.data:
                target_idx = i
                break
        return target_idx


class SettingsEchoOfWarView(SrBasicView, ft.Row):

    def __init__(self, ctx: Context):
        self.ctx: Context = ctx
        self.config = echo_of_war.get_config()

        plan_title = components.CardTitleText(gt('挑战规划', 'ui'))
        self.plan_list = PlanList(on_click_support=self.show_choose_support_character)
        plan_card = components.Card(self.plan_list, plan_title, width=800)

        self.character_card = CharacterInput(ctx.ih, max_chosen_num=1, on_value_changed=self._on_choose_support)
        self.character_card.visible = False

        ft.Row.__init__(self, controls=[plan_card, self.character_card], spacing=10)

        self.chosen_plan_item: Optional[PlanListItem] = None

    def handle_after_show(self):
        self.plan_list.refresh_by_config()

    def show_choose_support_character(self, target: PlanListItem):
        self.chosen_plan_item = target
        chosen_point: Optional[SurvivalIndexMission] = SurvivalIndexMissionEnum.get_by_unique_id(target.value['mission_id'])
        self.character_card.update_title('%s %s' % (gt('支援角色', 'ui'), chosen_point.ui_cn))
        chosen_list: List[str] = []
        if target.support_dropdown.value is not None and target.support_dropdown.value != 'none':
            chosen_list.append(target.support_dropdown.value)
        self.character_card.update_chosen_list(chosen_list)
        self.character_card.visible = True
        self.character_card.update()

    def _on_choose_support(self, chosen_id_list: List[str]):
        """
        选中角色后的回调 更新计划中的支援角色
        :param chosen_id_list:
        :return:
        """
        if self.chosen_plan_item is None:
            return

        self.chosen_plan_item.update_support(chosen_id_list[0] if len(chosen_id_list) > 0 else None)
        self.chosen_plan_item = None
        self.character_card.visible = False
        self.character_card.update()


_settings_echo_of_war_view: Optional[SettingsEchoOfWarView] = None


def get(ctx: Context) -> SettingsEchoOfWarView:
    global _settings_echo_of_war_view
    if _settings_echo_of_war_view is None:
        _settings_echo_of_war_view = SettingsEchoOfWarView(ctx)
    return _settings_echo_of_war_view


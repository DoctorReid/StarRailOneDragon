from typing import Callable, Optional, List

import flet as ft

from basic.i18_utils import gt
from basic.log_utils import log
from gui import components
from gui.components.character_input import CharacterInput
from gui.settings import gui_config
from gui.settings.gui_config import ThemeColors
from gui.sr_basic_view import SrBasicView
from sr.app.routine.forgotten_hall_app import ForgottenHallConfig, get_config, ForgottenHallTeamModule, \
    TEAM_MODULE_ATTACK, TEAM_MODULE_LIST
from sr.const.character_const import CHARACTER_LIST, QUANTUM, CHARACTER_COMBAT_TYPE_LIST
from sr.context import Context


class TeamListItem(ft.Row):

    def __init__(self, item: ForgottenHallTeamModule,
                 max_character_cnt: int = 4,
                 on_choose_team_member: Optional[Callable] = None,
                 on_click_del: Optional[Callable] = None,
                 on_value_changed: Optional[Callable] = None):

        self.team_value: ForgottenHallTeamModule = item
        self.value_changed_callback: Optional[Callable] = on_value_changed

        self.module_name_input = ft.TextField(label=gt('模块名称', 'ui'), value=self.team_value.module_name,
                                              width=80, on_change=self._on_module_name_changed)

        self.module_type_dropdown = ft.Dropdown(
            label=gt('模块', 'ui'), width=80,
            options=[ft.dropdown.Option(text=gt(i.module_name_cn, 'ui'), key=i.module_type) for i in TEAM_MODULE_LIST],
            value=self.team_value.module_type,
            on_change=self._on_module_type_changed
        )  # 暂时用不到

        self.combat_type_dropdown = ft.Dropdown(
            label=gt('应对属性', 'ui'), width=80,
            options=[ft.dropdown.Option(text=gt(i.cn, 'ui'), key=i.id) for i in CHARACTER_COMBAT_TYPE_LIST],
            value=self.team_value.combat_type,
            on_change=self._on_combat_type_changed
        )  # 暂时用不到

        self.character_dropdown_list: List[ft.Dropdown] = []
        for i in range(max_character_cnt):
            dropdown = ft.Dropdown(label='%s %d' % (gt('角色', 'ui'), (i + 1)),
                                   value='none', disabled=True, width=80,
                                   options=[ft.dropdown.Option(text='无', key='none')])
            for c in CHARACTER_LIST:
                dropdown.options.append(ft.dropdown.Option(text=gt(c.cn, 'ui'), key=c.id))
            self.character_dropdown_list.append(dropdown)

        self.del_btn = ft.IconButton(icon=ft.icons.DELETE_FOREVER_OUTLINED, data=id(self), on_click=on_click_del)

        controls = [self.module_name_input]
        for dropdown in self.character_dropdown_list:
            controls.append(ft.Container(content=dropdown, data=id(self), on_click=on_choose_team_member))
        controls.append(self.del_btn)

        super().__init__(controls=controls)

        self._update_character_dropdown_value()

    def _update(self):
        if self.page is not None:
            self.update()

    def _on_module_name_changed(self, e):
        """
        模块名称改变时的回调
        :param e:
        :return:
        """
        self.team_value.module_name = self.module_name_input.value
        self._on_value_changed()

    def _on_module_type_changed(self, e):
        """
        模块类型改变的回调
        :param e:
        :return:
        """
        self.team_value.module_type = self.module_type_dropdown.value
        self._on_value_changed()

    def _on_combat_type_changed(self, e):
        """
        应对属性改变的回调
        :param e:
        :return:
        """
        self.team_value.combat_type = self.combat_type_dropdown.value
        self._on_value_changed()

    def _on_value_changed(self):
        """
        整体任何改变往外的回调
        :return:
        """
        if self.value_changed_callback is not None:
            self.value_changed_callback(id(self))

    def _update_character_dropdown_value(self):
        """
        根据配队中的角色更新显示
        :return:
        """
        for i in range(len(self.character_dropdown_list)):
            dropdown = self.character_dropdown_list[i]
            if i < len(self.team_value.character_id_list):
                dropdown.value = self.team_value.character_id_list[i]
            else:
                dropdown.value = 'none'
        self._update()

    def update_team_member(self, character_id_list: List[str]):
        """
        更新配队角色列表
        :param character_id_list: 角色ID列表
        :return:
        """
        self.team_value.character_id_list.clear()  # 注意不能直接等于 因为这样会共用了同一个数组
        for character_id in character_id_list:
            self.team_value.character_id_list.append(character_id)
        self._update_character_dropdown_value()
        self._on_value_changed()


class TeamList(ft.ListView):

    def __init__(self, on_click_choose_member: Optional[Callable] = None):
        self.config: ForgottenHallConfig = get_config()
        plan_item_list: List[ForgottenHallTeamModule] = self.config.team_module_list

        super().__init__(controls=[self._list_view_item(i) for i in plan_item_list])
        self.add_btn = ft.Container(
            content=components.RectOutlinedButton(text='+', on_click=self._on_add_click),
            margin=ft.margin.only(top=5)
        )
        self.controls.append(self.add_btn)
        self._start_choose_member_callback: Optional[Callable] = on_click_choose_member

    def refresh_by_config(self):
        plan_item_list: List[ForgottenHallTeamModule] = self.config.team_module_list
        self.controls = [self._list_view_item(i) for i in plan_item_list]
        self.controls.append(self.add_btn)
        self.update()

    def _list_view_item(self, team: ForgottenHallTeamModule) -> ft.Container:
        """
        获取单行配队的组件
        :param team:
        :return:
        """
        theme: ThemeColors = gui_config.theme()
        return ft.Container(
                content=TeamListItem(team,
                                     on_choose_team_member=self._start_choose_member,
                                     on_value_changed=self._on_list_item_value_changed,
                                     on_click_del=self._on_item_click_del,
                                     ),
                border=ft.border.only(bottom=ft.border.BorderSide(1, theme['divider_color'])),
                padding=10
            )

    def _on_add_click(self, e):
        """
        添加一个新的配队
        :param e:
        :return:
        """
        # 新的队名
        new_module_name: str = ''
        for i in range(99):
            new_module_name = '%s%d' % (gt('模块', 'ui'), (i + 1))
            existed_name: bool = False  # 名称是否已经存在
            for item in self.controls:
                if type(item.content) == TeamListItem:
                    list_item: TeamListItem = item.content
                    if list_item.team_value.module_name == new_module_name:
                        existed_name = True
                        break
            if not existed_name:
                break

        new_team_value = ForgottenHallTeamModule(module_name=new_module_name, combat_type=QUANTUM.id,
                                                 module_type=TEAM_MODULE_ATTACK.module_type, character_id_list=[])
        new_list_item = self._list_view_item(new_team_value)
        self.controls.append(new_list_item)

        # 交换添加按钮
        last = len(self.controls) - 1
        tmp = self.controls[last - 1]
        self.controls[last - 1] = self.controls[last]
        self.controls[last] = tmp

        # 更新
        self.update()
        self._on_list_item_value_changed(id(new_list_item))

    def _get_list_item_component(self, component_id: int) -> Optional[TeamListItem]:
        """
        根据组件ID 获取对应的组件
        :param component_id: 组件ID
        :return:
        """
        for item in self.controls:
            if type(item.content) == TeamListItem and id(item.content) == component_id:
                return item.content
        return None

    def _start_choose_member(self, e):
        """
        开始为某个配队选择角色
        :param e: 点击事件
        :return:
        """
        component_id: int = e.control.data
        component = self._get_list_item_component(component_id)
        if component is None:  # 理论不可能的情况
            log.error('找不到配队组件 %d', component_id)
            return
        if self._start_choose_member_callback is not None:
            self._start_choose_member_callback(component)

    def _on_list_item_value_changed(self, component_id: Optional[int] = None):
        """
        配队改变后的回调
        需要更新配置
        :param component_id: 改变的组件ID
        :return:
        """
        team_list: List[ForgottenHallTeamModule] = []
        for item in self.controls:
            if type(item.content) == TeamListItem:
                component: TeamListItem = item.content
                team_list.append(component.team_value)
        self.config.team_module_list = team_list

    def _on_item_click_del(self, e):
        """
        配队删除后的回调
        需要更新配置
        :param e: 点击删除的事件
        :return:
        """
        component_id: int = e.control.data

        to_del_idx = -1
        for idx in range(len(self.controls)):
            if type(self.controls[idx].content) == TeamListItem and id(self.controls[idx].content) == component_id:
                to_del_idx = idx

        if to_del_idx != -1:
            self.controls.pop(to_del_idx)
            self.update()
            self._on_list_item_value_changed()


class SettingsForgottenHallView(SrBasicView, ft.Row):

    def __init__(self, page: ft.Page, ctx: Context):
        SrBasicView.__init__(self, page, ctx)
        team_card_title = components.CardTitleText(gt('配队规划', 'ui'))
        self.team_list = TeamList(on_click_choose_member=self._start_choose_member)
        team_card = components.Card(self.team_list, team_card_title, width=800)

        self.character_card = CharacterInput(ctx.ih, max_chosen_num=4)
        self.character_card.visible = False

        ft.Row.__init__(self, controls=[team_card, self.character_card], spacing=10)

        self.chosen_item: Optional[TeamListItem] = None

    def _start_choose_member(self, item: TeamListItem):
        """
        开始给某个配队选择角色
        :param item: 配队的组件 用于选择角色后回调
        :return:
        """
        self.chosen_item = None

        self.character_card.visible = True
        self.character_card.update_title(item.team_value.module_name)
        self.character_card.update_chosen_list(item.team_value.character_id_list)
        self.character_card.update_value_changed_callback(self._on_choose_member_changed)
        self.update()

        self.chosen_item = item

    def _on_choose_member_changed(self, character_id_list: List[str]):
        """
        当选择角色改变时 更新对应的配队
        :param character_id_list:
        :return:
        """
        self.chosen_item.update_team_member(character_id_list)


_settings_forgotten_hall_view: Optional[SettingsForgottenHallView] = None


def get(page: ft.Page, ctx: Context) -> SettingsForgottenHallView:
    global _settings_forgotten_hall_view
    if _settings_forgotten_hall_view is None:
        _settings_forgotten_hall_view = SettingsForgottenHallView(page, ctx)
    return _settings_forgotten_hall_view

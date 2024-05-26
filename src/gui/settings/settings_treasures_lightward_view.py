from typing import Callable, Optional, List

import flet as ft

from basic.i18_utils import gt
from basic.log_utils import log
from gui import components, snack_bar
from gui.components.character_input import CharacterInput
from gui.settings import gui_config
from gui.settings.gui_config import ThemeColors
from gui.sr_basic_view import SrBasicView
from sr.const.character_const import CHARACTER_LIST, get_character_by_id, CHARACTER_COMBAT_TYPE_LIST, \
    get_combat_type_by_id
from sr.context import Context
from sr.treasures_lightward.treasures_lightward_team_module import TreasuresLightwardTeamModule, \
    TlModuleItemCharacterTypeEnum, TlModuleItemPositionEnum, TreasuresLightwardTeamModuleItem


class TeamListItem(ft.Row):

    def __init__(self, item: TreasuresLightwardTeamModule,
                 max_character_cnt: int = 4,
                 on_choose_team_member: Optional[Callable] = None,
                 on_click_del: Optional[Callable] = None,
                 on_value_changed: Optional[Callable] = None):

        self.team_module: TreasuresLightwardTeamModule = item
        self.value_changed_callback: Optional[Callable] = on_value_changed

        self.module_name_input = ft.TextField(label=gt('名称', 'ui'), value=self.team_module.module_name,
                                              width=80, on_change=self._on_module_name_changed)

        self.character_text_list: List[ft.TextField] = [
            ft.TextField(label=gt('角色', 'ui'), value=gt('无', 'ui'),
                         disabled=True, width=90)
            for _ in range(max_character_cnt)
        ]

        self.combat_type_text: ft.TextField = ft.TextField(
            label=gt('应付属性', 'ui'), width=80, disabled=True
        )

        self.enable_fh = ft.Dropdown(label=gt('忘却之庭', 'ui'),
                                     value='true' if self.team_module.enable_fh else 'false', width=80,
                                     options=[
                                         ft.dropdown.Option(text=gt('启用', 'ui'), key='true'),
                                         ft.dropdown.Option(text=gt('禁用', 'ui'), key='false')
                                     ], on_change=self._on_fh_enable_changed)
        self.enable_pf = ft.Dropdown(label=gt('虚构叙事', 'ui'),
                                     value='true' if self.team_module.enable_pf else 'false', width=80,
                                     options=[
                                         ft.dropdown.Option(text=gt('启用', 'ui'), key='true'),
                                         ft.dropdown.Option(text=gt('禁用', 'ui'), key='false')
                                     ], on_change=self._on_pf_enable_changed)
        self.del_btn = ft.IconButton(icon=ft.icons.DELETE_FOREVER_OUTLINED, data=id(self), on_click=on_click_del)

        controls = [self.module_name_input]
        for text in self.character_text_list:
            controls.append(ft.Container(content=text, data=id(self), on_click=on_choose_team_member))
        controls.append(self.combat_type_text)
        controls.append(self.enable_fh)
        controls.append(self.enable_pf)
        controls.append(self.del_btn)

        super().__init__(controls=controls)
        self._update_display_by_module(update=False)

    def _update_display_by_module(self, update: bool = True):
        """
        根据配队 更新显示
        :return:
        """
        for i in range(len(self.team_module.character_list)):
            c = self.team_module.character_list[i]
            prefix = '角色' if c.character_type == TlModuleItemCharacterTypeEnum.AUTO else c.character_type.value
            suffix = '' if c.pos == TlModuleItemPositionEnum.AUTO else f'{c.pos.value}号位'
            full_label = gt(prefix, 'ui')
            if len(suffix) > 0:
                full_label += ' ' + gt(suffix, 'ui')
            self.character_text_list[i].label = full_label
            self.character_text_list[i].value = gt(c.character.cn, 'ui')

        self.module_name_input.value = self.team_module.module_name
        self.combat_type_text.value = self.team_module.combat_type_str
        self.enable_fh.value = 'true' if self.team_module.enable_fh else 'false'
        self.enable_pf.value = 'true' if self.team_module.enable_pf else 'false'

        if update:
            self.update()

    def _on_module_name_changed(self, e):
        """
        模块名称改变时的回调
        :param e:
        :return:
        """
        self.team_module.module_name = self.module_name_input.value
        self._on_value_changed()

    def _on_fh_enable_changed(self, e):
        """
        忘却之庭 启用/禁用
        :param e:
        :return:
        """
        self.team_module.enable_fh = self.enable_fh.value == 'true'
        self._on_value_changed()

    def _on_pf_enable_changed(self, e):
        """
        虚构叙事 启用/禁用
        :param e:
        :return:
        """
        self.team_module.enable_pf = self.enable_pf.value == 'true'
        self._on_value_changed()

    def _on_value_changed(self):
        """
        整体任何改变往外的回调
        :return:
        """
        if self.value_changed_callback is not None:
            self.value_changed_callback(id(self))

    def set_module(self, team_module: TreasuresLightwardTeamModule):
        """
        更新显示的配队模块
        :param team_module:
        :return:
        """
        self.team_module = team_module
        self._update_display_by_module()
        self._on_value_changed()


class TeamList(ft.ListView):

    def __init__(self, ctx: Context, on_click_choose_member: Optional[Callable] = None):
        self.ctx: Context = ctx
        plan_item_list: List[TreasuresLightwardTeamModule] = self.ctx.tl_config.team_module_list

        super().__init__(controls=[self._list_view_item(i) for i in plan_item_list])
        self.add_btn = ft.Container(
            content=components.RectOutlinedButton(text='+', on_click=self._on_add_click),
            margin=ft.margin.only(top=5)
        )
        self.controls.append(self.add_btn)
        self._start_choose_member_callback: Optional[Callable] = on_click_choose_member

    def refresh_by_config(self):
        plan_item_list: List[TreasuresLightwardTeamModule] = self.ctx.tl_config.team_module_list
        self.controls = [self._list_view_item(i) for i in plan_item_list]
        self.controls.append(self.add_btn)
        self.update()

    def _list_view_item(self, team: TreasuresLightwardTeamModule) -> ft.Container:
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
                    if list_item.team_module.module_name == new_module_name:
                        existed_name = True
                        break
            if not existed_name:
                break

        new_team_module = TreasuresLightwardTeamModule(module_name=new_module_name)
        new_list_item = self._list_view_item(new_team_module)
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
        team_list: List[TreasuresLightwardTeamModule] = []
        for item in self.controls:
            if type(item.content) == TeamListItem:
                component: TeamListItem = item.content
                team_list.append(component.team_module)
        self.ctx.tl_config.team_module_list = team_list

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


class TeamEditCard(components.Card):

    def __init__(self,
                 character_input: CharacterInput,
                 max_character_cnt: int = 4,
                 on_save: Optional[Callable[[Optional[TreasuresLightwardTeamModule]], None]] = None):
        """
        编辑组队模块
        :param character_input:
        :param max_character_cnt:
        :param on_save: 点击保存时 回传新的配队；点击取消时 回传None
        """
        self.character_input: CharacterInput = character_input
        self.team_module: TreasuresLightwardTeamModule = TreasuresLightwardTeamModule()

        self.module_name_input = ft.TextField()

        self.character_dropdown_list: List[ft.Dropdown] = []
        for i in range(max_character_cnt):
            dropdown = ft.Dropdown(label=gt('角色', 'ui'), data=i,
                                   value='none', disabled=True, width=150,
                                   options=[ft.dropdown.Option(text='无', key='none')])
            for c in CHARACTER_LIST:
                dropdown.options.append(ft.dropdown.Option(text=gt(c.cn, 'ui'), key=c.id))
            self.character_dropdown_list.append(dropdown)

        self.character_type_dropdown_list: List[ft.Dropdown] = [
            ft.Dropdown(label=gt('角色类型', 'ui'), value='AUTO', width=80,
                        options=[ft.dropdown.Option(text=i.value, key=i.name) for i in TlModuleItemCharacterTypeEnum])
            for _ in range(max_character_cnt)
        ]

        self.character_pos_dropdown_list: List[ft.Dropdown] = [
            ft.Dropdown(label=gt('角色站位', 'ui'), value='AUTO', width=80,
                        options=[ft.dropdown.Option(text=i.value, key=i.name) for i in TlModuleItemPositionEnum])
            for _ in range(max_character_cnt)
        ]

        self.combat_type_checkbox_list: List[ft.Checkbox] = []
        self.ct_2_check_box: dict[str, ft.Checkbox] = {}
        for ct in CHARACTER_COMBAT_TYPE_LIST:
            cb = ft.Checkbox(label=gt(ct.cn, 'ui'), value=False, data=ct.id)
            self.combat_type_checkbox_list.append(cb)
            self.ct_2_check_box[ct.id] = cb

        self.enable_fh = ft.Dropdown(label=gt('忘却之庭', 'ui'),
                                     value='true', width=80,
                                     options=[
                                         ft.dropdown.Option(text=gt('启用', 'ui'), key='true'),
                                         ft.dropdown.Option(text=gt('禁用', 'ui'), key='false')
                                     ])
        self.enable_pf = ft.Dropdown(label=gt('虚构叙事', 'ui'),
                                     value='true', width=80,
                                     options=[
                                         ft.dropdown.Option(text=gt('启用', 'ui'), key='true'),
                                         ft.dropdown.Option(text=gt('禁用', 'ui'), key='false')
                                     ])

        self.character_row_list: List[ft.Row] = [
            ft.Row(controls=[
                # Dropdown没有click事件 要包一层
                ft.Container(content=self.character_dropdown_list[i], on_click=self._to_select_character, data=i),
                self.character_type_dropdown_list[i],
                self.character_pos_dropdown_list[i]
            ])
            for i in range(max_character_cnt)
        ]

        self.save_btn = components.RectOutlinedButton(text=gt('保存', 'ui'), on_click=self._on_save_click)
        self.cancel_btn = components.RectOutlinedButton(text=gt('取消', 'ui'), on_click=self._on_cancel_click)

        self.settings_list = components.SettingsList(
            controls=
            [
                components.SettingsListItem(gt('模块名称', 'ui'), self.module_name_input),
                components.SettingsListItem('关卡', ft.Row(controls=[self.enable_fh, self.enable_pf])),
            ] +
            [
                components.SettingsListItem(
                    label=gt('应对属性', 'ui') if page_num == 0 else '',
                    value_component=ft.Row(controls=[
                        self.combat_type_checkbox_list[idx]
                        for idx in range(page_num * 4, page_num * 4 + 4)
                        if idx < len(self.combat_type_checkbox_list)
                    ]))
                for page_num in range((len(self.combat_type_checkbox_list) // 4) + 1)
            ] +
            [
                components.SettingsListItem('%s %d' % (gt('角色', 'ui'), (i + 1)), self.character_row_list[i])
                for i in range(max_character_cnt)
            ] +
            [
                components.SettingsListItem('', ft.Row(controls=[self.save_btn, self.cancel_btn])),
            ],
            width=400
        )

        components.Card.__init__(self, content=self.settings_list)

        self._save_callback: Optional[Callable[[Optional[TreasuresLightwardTeamModule]], None]] = on_save
        self.selected_idx: int = 0  # 当前选择更改的角色下标

    def update_display_by_module(self):
        """
        根据配置模块 更新显示内容
        :return:
        """
        self.module_name_input.value = self.team_module.module_name

        for cb in self.combat_type_checkbox_list:
            cb.value = False
        for ct in self.team_module.combat_type_list:
            self.ct_2_check_box[ct.id].value = True

        self.enable_fh.value = 'true' if self.team_module.enable_fh else 'false'
        self.enable_pf.value = 'true' if self.team_module.enable_pf else 'false'

        for i in range(len(self.character_dropdown_list)):
            if i < len(self.team_module.character_list):
                module_item: TreasuresLightwardTeamModuleItem = self.team_module.character_list[i]
                self.character_dropdown_list[i].value = module_item.character_id
                self.character_type_dropdown_list[i].value = module_item.character_type.name
                self.character_pos_dropdown_list[i].value = module_item.pos.name
            else:
                self.character_dropdown_list[i].value = 'none'
                self.character_type_dropdown_list[i].value = 'AUTO'
                self.character_pos_dropdown_list[i].value = 'AUTO'

        self.update()

    def set_module(self, team_module: TreasuresLightwardTeamModule):
        """
        更新显示的配队模块
        :param team_module:
        :return:
        """
        self.team_module = team_module
        self.update_display_by_module()

    def _on_save_click(self, e):
        """
        触发保存
        :param e:
        :return:
        """
        err_message: str = ''  # 错误信息
        module = TreasuresLightwardTeamModule()

        module.module_name = self.module_name_input.value
        module.combat_type_list = [
            get_combat_type_by_id(cb.data)
            for cb in self.combat_type_checkbox_list
            if cb.value
        ]
        module.enable_fh = self.enable_fh.value == 'true'
        module.enable_pf = self.enable_pf.value == 'true'

        character_id_set = set()

        for i in range(len(self.character_dropdown_list)):
            character_id = self.character_dropdown_list[i].value
            if character_id == 'none':
                continue
            if character_id in character_id_set:
                err_message += '不能有重复角色'
                break
            character_id_set.add(character_id)
            item = TreasuresLightwardTeamModuleItem(
                character_id=self.character_dropdown_list[i].value,
                character_type=self.character_type_dropdown_list[i].value,
                pos=self.character_pos_dropdown_list[i].value
            )
            module.character_list.append(item)

        if len(err_message) > 0:
            snack_bar.show_message(err_message, self.page)
            return

        module.character_list = sorted(module.character_list, key=lambda x: x.pos.value)

        if self._save_callback is not None:
            self._save_callback(module)

    def _on_cancel_click(self, e):
        """
        触发取消
        :param e:
        :return:
        """
        if self._save_callback is not None:
            self._save_callback(None)

    def _to_select_character(self, e):
        """
        点击角色名后触发显示角色输入框
        :param e:
        :return:
        """
        self.selected_idx = e.control.data

        self.character_input.visible = True
        self.character_input.update_title(gt(f'角色 {self.selected_idx}', 'ui'))
        self.character_input.update_chosen_list([self.character_dropdown_list[self.selected_idx].value])
        self.character_input.update_value_changed_callback(self._on_member_changed)

        self.update()

    def _on_member_changed(self, character_id_list: List[str]):
        self.character_dropdown_list[self.selected_idx].value = character_id_list[0] if len(character_id_list) > 0 else 'none'
        self.character_input.visible = False

        self.update()


class SettingsTreasuresLightwardView(SrBasicView, ft.Row):

    def __init__(self, page: ft.Page, ctx: Context):
        SrBasicView.__init__(self, page, ctx)
        team_card_title = components.CardTitleText(gt('配队规划', 'ui'))
        self.team_list = TeamList(self.sr_ctx, on_click_choose_member=self._edit_team_module)
        self.team_card = components.Card(self.team_list, team_card_title, width=800)

        self.character_card = CharacterInput(ctx.ih, max_chosen_num=1)
        self.character_card.visible = False

        self.team_module_card = TeamEditCard(character_input=self.character_card, on_save=self._on_team_updated)
        self.team_module_card.visible = False

        ft.Row.__init__(self, controls=[self.team_card,
                                        self.team_module_card,
                                        self.character_card], spacing=10)

        self.chosen_item: Optional[TeamListItem] = None

    def handle_after_show(self):
        self.team_list.refresh_by_config()

    def _edit_team_module(self, item: TeamListItem):
        """
        触发修改某个配队
        :param item: 配队的组件 用于选择角色后回调
        :return:
        """
        self.chosen_item = item
        self.team_card.visible = False
        self.team_module_card.visible = True
        self.team_module_card.set_module(self.chosen_item.team_module)

    def _on_team_updated(self, team_module: Optional[TreasuresLightwardTeamModule]):
        """
        编辑配队后的更新回调
        :param team_module:
        :return:
        """
        self.team_card.visible = True
        self.team_module_card.visible = False

        if team_module is not None:
            self.chosen_item.set_module(team_module)
        else:
            self.update()


_settings_treasures_lightward_view: Optional[SettingsTreasuresLightwardView] = None


def get(page: ft.Page, ctx: Context) -> SettingsTreasuresLightwardView:
    global _settings_treasures_lightward_view
    if _settings_treasures_lightward_view is None:
        _settings_treasures_lightward_view = SettingsTreasuresLightwardView(page, ctx)
    return _settings_treasures_lightward_view

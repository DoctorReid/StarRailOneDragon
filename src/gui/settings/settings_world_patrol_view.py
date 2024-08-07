from typing import Optional

import flet as ft

from basic.i18_utils import gt
from gui import components
from gui.components import SettingsListItem, SettingsList
from gui.sr_basic_view import SrBasicView
from sr.app.world_patrol.world_patrol_whitelist_config import WorldPatrolWhitelist, load_all_whitelist_id
from sr.context.context import Context


class SettingsWorldPatrolView(SrBasicView, components.Card):

    def __init__(self, page: ft.Page, ctx: Context):
        SrBasicView.__init__(self, page, ctx)

        plan_title = components.CardTitleText(gt('锄大地', 'ui'))

        self.team_num_dropdown = ft.Dropdown(options=[ft.dropdown.Option(text=str(i), key=str(i)) for i in range(10)],
                                             on_change=self._on_team_num_changed)
        self.whitelist_dropdown = ft.Dropdown(on_change=self._on_whitelist_changed)
        self.tech_fight_cb = ft.Checkbox(on_change=self._on_tech_fight_changed)
        self.tech_only_cb = ft.Checkbox(on_change=self._on_tech_only_changed)
        self.max_consumable_cnt = ft.Dropdown(options=[ft.dropdown.Option(key=str(i), text=str(i)) for i in range(6)],
                                              on_change=self._on_max_consumable_cnt_changed)
        self.radiant_feldspar_name = ft.Dropdown(options=[ft.dropdown.Option(text=i, key=i) for i in ['晖长石号', '塔塔洛夫号', '开拓之尾号', '飞翔时针号']], on_change=self._on_radiant_feldspar_name_change)

        self.plan_list = SettingsList(
            controls=[
                SettingsListItem('使用配队', self.team_num_dropdown),
                SettingsListItem('特定路线名单', self.whitelist_dropdown),
                SettingsListItem('秘技开怪', self.tech_fight_cb),
                SettingsListItem('仅秘技开怪', self.tech_only_cb),
                SettingsListItem('单次最多消耗品个数', self.max_consumable_cnt),
                SettingsListItem('晖长石号名称', self.radiant_feldspar_name),
            ],
            width=400
        )

        components.Card.__init__(self, self.plan_list, plan_title, width=800)

    def handle_after_show(self):
        self._load_whitelist()
        self._init_by_config()


    def _load_whitelist(self):
        """
        读取名单列表
        :return:
        """
        whitelist_id_list = load_all_whitelist_id()
        options = [ft.dropdown.Option(text='无', key='none')]
        for whitelist_id in whitelist_id_list:
            whitelist = WorldPatrolWhitelist(whitelist_id)
            opt = ft.dropdown.Option(text=whitelist.name, key=whitelist.id)
            options.append(opt)
        self.whitelist_dropdown.options = options
        self.update()

    def _init_by_config(self):
        config = self.sr_ctx.world_patrol_config
        self.team_num_dropdown.value = str(config.team_num)
        self.whitelist_dropdown.value = config.whitelist_id
        self.tech_fight_cb.value = config.technique_fight
        self.tech_only_cb.value = config.technique_only
        self.max_consumable_cnt.value = str(config.max_consumable_cnt)
        self.radiant_feldspar_name.value = str(config.radiant_feldspar_name)
        self.update()

    def _on_team_num_changed(self, e):
        """
        使用配队变更
        :param e:
        :return:
        """
        self.sr_ctx.world_patrol_config.team_num = int(self.team_num_dropdown.value)

    def _on_whitelist_changed(self, e):
        """
        特定路线名单变更
        :param e:
        :return:
        """
        self.sr_ctx.world_patrol_config.whitelist_id = self.whitelist_dropdown.value

    def _on_tech_fight_changed(self, e):
        """
        秘技开怪变更
        :param e:
        :return:
        """
        self.sr_ctx.world_patrol_config.technique_fight = self.tech_fight_cb.value

    def _on_tech_only_changed(self, e):
        """
        仅秘技开怪变更
        :param e:
        :return:
        """
        self.sr_ctx.world_patrol_config.technique_only = self.tech_only_cb.value

    def _on_max_consumable_cnt_changed(self, e):
        """
        单次使用消耗品个数
        :param e:
        :return:
        """
        self.sr_ctx.world_patrol_config.max_consumable_cnt = int(self.max_consumable_cnt.value)

    def _on_radiant_feldspar_name_change(self, e):
        """
        晖长石号名称
        :param e:
        :return:
        """
        self.sr_ctx.world_patrol_config.radiant_feldspar_name = self.radiant_feldspar_name.value


_settings_world_patrol_view: Optional[SettingsWorldPatrolView] = None

def get(page: ft.Page, ctx: Context) -> SettingsWorldPatrolView:
    global _settings_world_patrol_view
    if _settings_world_patrol_view is None:
        _settings_world_patrol_view = SettingsWorldPatrolView(page, ctx)
    return _settings_world_patrol_view

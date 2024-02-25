from typing import Optional, Callable

import flet as ft

import sr.one_dragon_config
from basic import os_utils
from basic.i18_utils import gt
from basic.log_utils import log
from gui import components, version, snack_bar
from gui.settings import gui_config
from gui.settings.gui_config import GuiConfig
from gui.sr_basic_view import SrBasicView
from sr.context import Context
from sr.one_dragon_config import OneDragonAccount


class AccountListItem(ft.Container):

    def __init__(self, ctx: Context,
                 account: OneDragonAccount,
                 on_change: Optional[Callable[[OneDragonAccount], None]] = None,
                 on_active: Optional[Callable[[int], None]] = None,
                 on_delete: Optional[Callable[[int], None]] = None):
        theme = gui_config.theme()
        id_text = ft.Text(value='编号' + ('%02d' % account.idx))
        self.name_input = ft.TextField(label='名称', value=account.name, width=80,
                                       disabled=ctx.is_running, on_change=self._on_name_changed)
        self.active_now = components.RectOutlinedButton(
            text='当前启用' if account.active else '启用',
            disabled=ctx.is_running or account.active,
            on_click=self._on_active_now_changed
        )
        self.del_btn = ft.IconButton(icon=ft.icons.DELETE_FOREVER_OUTLINED,
                                     disabled=ctx.is_running or account.active,
                                     on_click=self._on_click_delete)
        self.active_in_od = ft.Checkbox(label='加入一条龙', value=account.active_in_od,
                                        disabled=ctx.is_running,
                                        on_change=self._on_active_in_od_changed)

        ft.Container.__init__(
            self,
            content=ft.Row(controls=[id_text, self.name_input, self.active_now, self.active_in_od, self.del_btn]),
            border=ft.border.only(bottom=ft.border.BorderSide(1, theme['divider_color'])),
            padding=10
        )

        self.ctx: Context = ctx
        self.on_change: Optional[Callable[[OneDragonAccount], None]] = on_change
        self.on_active: Optional[Callable[[int], None]] = on_active
        self.on_delete: Optional[Callable[[int], None]] = on_delete
        self.account: OneDragonAccount = account

    def _on_value_changed(self):
        """
        值改变后的回调
        :return:
        """
        if self.on_change is not None:
            self.on_change(self.account)

    def _on_name_changed(self, e):
        """
        名字改变
        :return:
        """
        self.account.name = self.name_input.value
        self._on_value_changed()

    def _on_active_now_changed(self, e):
        """
        当前启用改变
        :return:
        """
        if self.on_active is not None:
            self.on_active(self.account.idx)

    def _on_active_in_od_changed(self, e):
        """
        加入一条龙改变
        :return:
        """
        self.account.active_in_od = self.active_in_od.value
        self._on_value_changed()

    def _on_click_delete(self, e):
        """
        点击删除
        :param e:
        :return:
        """
        if self.on_delete is not None:
            self.on_delete(self.account.idx)

    def update_account(self, account: OneDragonAccount):
        self.account = account

        self.name_input.value = self.account.name
        self.name_input.disabled = self.ctx.is_running

        self.active_now.text = '当前启用' if self.account.active else '启用'
        self.active_now.disabled = self.ctx.is_running or self.account.active

        self.active_in_od.value = self.account.active_in_od
        self.active_in_od.disabled = self.ctx.is_running

        self.del_btn.disabled = self.ctx.is_running or self.account.active

        self.update()


class SettingsBasicView(components.Card, SrBasicView):

    def __init__(self, page: ft.Page, ctx: Context):
        SrBasicView.__init__(self, page, ctx)

        self.gui_config: GuiConfig = gui_config.get()
        self.gui_theme_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option(text=gt(i.cn, 'ui'), key=i.id) for i in gui_config.ALL_GUI_THEME_LIST],
            value=self.gui_config.theme,
            width=200, on_change=self._on_ui_theme_changed
        )

        self.debug_mode_check = ft.Checkbox(label=gt('调试模式', 'ui'), on_change=self._on_debug_mode_changed)

        self.check_update_btn = components.RectOutlinedButton(text='检查更新', on_click=self.check_update)
        self.update_btn = components.RectOutlinedButton(text='更新', on_click=self.do_update, visible=False)
        self.pre_release_switch = ft.Switch(value=False, on_change=self.on_prerelease_switch)
        self.proxy_type_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option(text=gt(i.cn, 'ui'), key=i.id) for i in sr.one_dragon_config.PROXY_TYPE_LIST
            ],
            width=150, on_change=self._on_proxy_type_changed
        )
        self.personal_proxy_input = ft.TextField(hint_text='host:port', width=150,
                                                 value='http://127.0.0.1:8234', disabled=True,
                                                 on_change=self._on_personal_proxy_changed)

        self.width: int = 400
        self.add_btn = components.RectOutlinedButton(text='+', on_click=self.on_account_added)

        self.settings_item_list = ft.ListView(controls=[
            components.SettingsListGroupTitle('基础'),
            components.SettingsListItem('界面主题', self.gui_theme_dropdown),
            components.SettingsListItem('调试模式', self.debug_mode_check),
            components.SettingsListGroupTitle('更新'),
            components.SettingsListItem('测试版本', self.pre_release_switch),
            components.SettingsListItem('代理类型', self.proxy_type_dropdown),
            components.SettingsListItem('代理地址', self.personal_proxy_input),
            components.SettingsListItem('检查更新', ft.Row(controls=[self.check_update_btn, self.update_btn])),
            components.SettingsListGroupTitle('脚本账号列表'),
            components.SettingsListItem('', self.add_btn),
        ], width=self.width)

        components.Card.__init__(self, self.settings_item_list, width=500)

    def handle_after_show(self):
        self._load_config_and_display()

    def _load_config_and_display(self):
        """
        加载配置显示
        :return:
        """
        self.debug_mode_check.value = self.sr_ctx.one_dragon_config.is_debug

        self.proxy_type_dropdown.value = self.sr_ctx.one_dragon_config.proxy_type
        self.personal_proxy_input.value = self.sr_ctx.one_dragon_config.personal_proxy
        self._update_proxy_part_display()

        self._init_account_list()

    def _init_account_list(self):
        """
        初始化账号列表 加载、增加、删除时候使用
        :return:
        """
        # 清空掉账号条目
        while True:
            item = self.settings_item_list.controls[-2]
            if type(item) == components.SettingsListGroupTitle:  # 最后一个标题应该是 '脚本账号列表'
                break
            self.settings_item_list.controls.pop(-2)

        for account in self.sr_ctx.one_dragon_config.account_list:
            self.settings_item_list.controls.insert(
                -1,
                AccountListItem(self.sr_ctx, account,
                                on_change=self.on_account_value_changed,
                                on_active=self.on_account_actived,
                                on_delete=self.on_account_deleted)
            )
        self.settings_item_list.update()

    def on_account_value_changed(self, account: OneDragonAccount):
        """
        账号资料改变
        :param account:
        :return:
        """
        self.sr_ctx.one_dragon_config.update_account(account)

    def on_account_actived(self, account_idx: int):
        self.sr_ctx.active_account(account_idx)  # 这一步会改变 config.account_list 的值
        self._update_account_list_display()

    def on_account_added(self, e):
        """
        新增一个账号
        :return:
        """
        account = self.sr_ctx.one_dragon_config.create_new_account(False)
        self.settings_item_list.controls.insert(-1, AccountListItem(self.sr_ctx, account,
                                                                    on_change=self.on_account_value_changed,
                                                                    on_active=self.on_account_actived,
                                                                    on_delete=self.on_account_deleted))
        self.settings_item_list.update()
        self._update_account_list_display()

    def on_account_deleted(self, account_idx: int):
        """
        删除账号
        :param account_idx:
        :return:
        """
        self.sr_ctx.one_dragon_config.delete_account(account_idx)

        idx = -1
        for i in range(len(self.settings_item_list.controls)):
            item: AccountListItem = self.settings_item_list.controls[i]
            if type(item) != AccountListItem:
                continue
            if item.account.idx == account_idx:
                idx = i
                break

        if idx != -1:
            self.settings_item_list.controls.pop(idx)
            self.settings_item_list.update()
            self._update_account_list_display()

    def _update_account_list_display(self):
        """
        跟价配置中的账号列表 更新页面的显示
        在 one_dragon_config.account_list 改变时需要调用
        - 增加账号
        - 删除账号
        - 激活账号
        :return:
        """
        for item in self.settings_item_list.controls:
            if type(item) != AccountListItem:
                continue
            for account in self.sr_ctx.one_dragon_config.account_list:
                if account.idx == item.account.idx:
                    item.update_account(account)
                    break

    def _on_ui_theme_changed(self, e):
        """
        UI主题改变
        :param e:
        :return:
        """
        self.gui_config.theme = self.gui_theme_dropdown.value

    def _on_debug_mode_changed(self, e):
        self.sr_ctx.one_dragon_config.is_debug = self.debug_mode_check.value

    def on_prerelease_switch(self, e):
        if self.pre_release_switch.value:
            msg: str = gt('测试版可能功能不稳定 如遇问题，可关闭后再次更新', 'ui')
            snack_bar.show_message(msg, self.flet_page)
            log.info(msg)

    def check_update(self, e):
        version_result = version.check_new_version(proxy=self.sr_ctx.one_dragon_config.proxy_address,
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
        self.sr_ctx.one_dragon_config.proxy_type = self.proxy_type_dropdown.value
        self._update_proxy_part_display()

    def _on_personal_proxy_changed(self, e):
        self.sr_ctx.one_dragon_config.personal_proxy = self.personal_proxy_input.value


_settings_basic_view: Optional[SettingsBasicView] = None


def get(page: ft.Page, ctx: Context) -> SettingsBasicView:
    global _settings_basic_view
    if _settings_basic_view is None:
        _settings_basic_view = SettingsBasicView(page, ctx)

    return _settings_basic_view

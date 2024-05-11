from typing import Optional, Callable, List

import flet as ft

import sr.image.yolo_screen_detector
from basic.i18_utils import gt
from basic.log_utils import log
from gui import components, snack_bar
from gui.settings import gui_config
from gui.settings.gui_config import GuiConfig
from gui.sr_basic_view import SrBasicView
from sr.app.switch_account.switch_account_app import SwitchAccountApp
from sr.context import Context
from sr.one_dragon_config import OneDragonAccount
from sryolo.detector import check_model_exists, get_model_dir_path

_AVAILABLE_YOLO_LIST: List[str] = [
    'yolov8n-1088-full-0428'
]


class AccountListItem(ft.Container):

    def __init__(self, ctx: Context,
                 account: OneDragonAccount,
                 on_change: Optional[Callable[[OneDragonAccount], None]] = None,
                 on_active: Optional[Callable[[int], None]] = None,
                 on_delete: Optional[Callable[[int], None]] = None,
                 on_switch: Optional[Callable[[int], None]] = None
                 ):
        theme = gui_config.theme()
        id_text = ft.Text(value='编号' + ('%02d' % account.idx))
        self.name_input = ft.TextField(label='名称', value=account.name, width=80,
                                       disabled=ctx.is_running, on_change=self._on_name_changed)
        self.active_now = components.RectOutlinedButton(
            text='当前' if account.active else '启用',
            disabled=ctx.is_running or account.active,
            on_click=self._on_active_now_changed
        )
        self.del_btn = ft.IconButton(icon=ft.icons.DELETE_FOREVER_OUTLINED,
                                     disabled=ctx.is_running or account.active,
                                     on_click=self._on_click_delete)
        self.active_in_od = ft.Dropdown(label='一条龙',
                                        options=[
                                            ft.dropdown.Option(key='True', text='是'),
                                            ft.dropdown.Option(key='False', text='否'),
                                        ],
                                        value=str(account.active_in_od),
                                        disabled=ctx.is_running,
                                        on_change=self._on_active_in_od_changed,
                                        width=65
                                        )
        self.switch_btn = components.RectOutlinedButton(
            text='登陆',
            disabled=ctx.is_running or not account.active,
            on_click=self._on_switch_clicked
        )

        ft.Container.__init__(
            self,
            content=ft.Row(controls=[id_text, self.name_input, self.active_now, self.switch_btn, self.active_in_od, self.del_btn]),
            border=ft.border.only(bottom=ft.border.BorderSide(1, theme['divider_color'])),
            padding=10
        )

        self.ctx: Context = ctx
        self.on_change: Optional[Callable[[OneDragonAccount], None]] = on_change
        self.on_active: Optional[Callable[[int], None]] = on_active
        self.on_delete: Optional[Callable[[int], None]] = on_delete
        self.on_switch: Optional[Callable[[int], None]] = on_switch
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

    def _on_switch_clicked(self, e):
        """
        登陆另一个账号
        :param e:
        :return:
        """
        if self.on_switch is not None:
            self.on_switch(self.account.idx)

    def _on_active_in_od_changed(self, e):
        """
        加入一条龙改变
        :return:
        """
        self.account.active_in_od = self.active_in_od.value == 'True'
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

        self.active_now.text = '当前' if self.account.active else '启用'
        self.active_now.disabled = self.ctx.is_running or self.account.active

        self.active_in_od.value = str(self.account.active_in_od)
        self.active_in_od.disabled = self.ctx.is_running

        self.del_btn.disabled = self.ctx.is_running or self.account.active

        self.switch_btn.disabled = self.ctx.is_running or not self.account.active

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
        self.yolo_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option(key=i, text=i) for i in _AVAILABLE_YOLO_LIST],
            on_change=self._on_yolo_changed,
            width=250
        )
        self.yolo_download_btn = components.RectOutlinedButton(text='下载', on_click=self._download_yolo_model)

        self.width: int = 450
        self.add_btn = components.RectOutlinedButton(text='+', on_click=self.on_account_added)

        self.settings_item_list = ft.ListView(controls=[
            components.SettingsListGroupTitle('基础'),
            components.SettingsListItem('界面主题', self.gui_theme_dropdown),
            components.SettingsListItem('YOLO模型', ft.Row(controls=[self.yolo_dropdown, self.yolo_download_btn])),
            components.SettingsListItem('调试模式', self.debug_mode_check),
            components.SettingsListGroupTitle('脚本账号列表'),
            components.SettingsListItem('', self.add_btn),
        ], width=self.width)

        components.Card.__init__(self, self.settings_item_list, width=550)

    def handle_after_show(self):
        self._load_config_and_display()

    def _load_config_and_display(self):
        """
        加载配置显示
        :return:
        """
        self.debug_mode_check.value = self.sr_ctx.one_dragon_config.is_debug
        self.yolo_dropdown.value = self.sr_ctx.one_dragon_config.yolo_model
        if self.yolo_dropdown.value == '' or self.yolo_dropdown.value is None:
            self.yolo_download_btn.disabled = True
        else:
            self.yolo_download_btn.disabled = check_model_exists(
                sr.image.yolo_screen_detector.get_yolo_model_parent_dir(), self.yolo_dropdown.value)

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
                                on_delete=self.on_account_deleted,
                                on_switch=self.on_account_switch,
                                )
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

    def _on_yolo_changed(self, e):
        """
        选择的yolo模型改变时
        :param e:
        :return:
        """
        model_name = self.yolo_dropdown.value
        self.sr_ctx.one_dragon_config.yolo_model = model_name
        existed = check_model_exists(sr.image.yolo_screen_detector.get_yolo_model_parent_dir(), model_name)
        self.yolo_download_btn.disabled = existed
        self.yolo_download_btn.update()
        if not existed:
            msg = 'YOLO模型未存在 请先下载'
            snack_bar.show_message(msg, self.flet_page)
            log.warn(msg)

    def _download_yolo_model(self, e):
        """
        下载YOLO模型
        :param e:
        :return:
        """
        msg = '准备下载YOLO模型 下载慢可以手动到QQ群里下载'
        snack_bar.show_message(msg, self.flet_page)
        log.info(msg)
        model_name = self.yolo_dropdown.value
        log.info(f'下载后 模型存放在 model/yolo/{model_name}/ 文件夹中，里面包含2个文件 model.onnx 和 labels.csv')
        get_model_dir_path(sr.image.yolo_screen_detector.get_yolo_model_parent_dir(), model_name)
        existed = check_model_exists(sr.image.yolo_screen_detector.get_yolo_model_parent_dir(), model_name)
        self.yolo_download_btn.disabled = existed
        self.yolo_download_btn.update()
        if existed:
            msg = 'YOLO模型下载成功'
        else:
            msg = 'YOLO模型下载失败 请重试'
        snack_bar.show_message(msg, self.flet_page)
        log.info(msg)

    def on_account_switch(self, account_idx: int):
        app = SwitchAccountApp(self.sr_ctx, account_idx)
        op_result = app.execute()
        log.info('切换账号登录完成 %s', ('成功' if op_result.success else '失败'))
        self.handle_after_show()  # 运行后重新加载本页面


_settings_basic_view: Optional[SettingsBasicView] = None


def get(page: ft.Page, ctx: Context) -> SettingsBasicView:
    global _settings_basic_view
    if _settings_basic_view is None:
        _settings_basic_view = SettingsBasicView(page, ctx)

    return _settings_basic_view

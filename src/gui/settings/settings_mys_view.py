from typing import Optional

import flet as ft

from basic.i18_utils import gt
from basic.log_utils import log
from gui import components, snack_bar
from gui.sr_basic_view import SrBasicView
from sr.context import Context


class SettingsMysView(SrBasicView, ft.Row):

    def __init__(self, page: ft.Page, ctx: Context):
        SrBasicView.__init__(self, page, ctx)
        self.account_phone_text = ft.Text()
        self.logout_btn = components.RectOutlinedButton(gt('注销', 'ui'), on_click=self._on_click_logout)
        self.show_qrcode_btn = components.RectOutlinedButton(text='二维码登录', on_click=self._on_click_qrcode)
        account_row_right = ft.Row(controls=[self.account_phone_text, self.logout_btn, self.show_qrcode_btn])

        self.auto_game_sign = ft.Checkbox(on_change=self._on_auto_game_sign_changed)
        self.auto_bbs_sign = ft.Checkbox(on_change=self._on_auto_bbs_sign_changed)
        self.sign_text = ft.Text(value='发送 #签到 即可')

        setting_list = components.SettingsList(controls=[
            components.SettingsListItem(gt('账号状态', 'ui'), account_row_right),

            components.SettingsListItem(gt('签到推荐使用QQ群机器人', 'ui'), self.sign_text),
            # components.SettingsListItem(gt('自动游戏签到', 'ui'), self.auto_game_sign),
            # components.SettingsListItem(gt('自动米游币任务', 'ui'), self.auto_bbs_sign),
        ])
        settings_card_title = components.CardTitleText(title=gt('米游社', 'ui'))
        settings_card = components.Card(setting_list, title=settings_card_title, width=400)

        self.qrcode_img = ft.Image(src="a.png", fit=ft.ImageFit.CONTAIN, error_content=ft.Text('等待加载二维码'), visible=False)
        login_card_content = ft.Column(controls=[self.qrcode_img])
        login_card_title = components.CardTitleText(title=gt('登录', 'ui'))
        self.login_card = components.Card(login_card_content, title=login_card_title, width=250)

        ft.Row.__init__(self, controls=[settings_card, self.login_card], spacing=10)

    def handle_after_show(self):
        self._update_login_related_components()

    def _update_login_related_components(self):
        """
        更新登录账号相关的组件状态
        :return:
        """
        is_login = self.sr_ctx.mys_config.is_login
        self.account_phone_text.visible = is_login
        self.account_phone_text.value = self.sr_ctx.mys_config.phone_number if is_login else '未登录'
        self.logout_btn.visible = is_login
        self.login_card.visible = not is_login
        self.show_qrcode_btn.visible = not is_login

        self.auto_game_sign.value = self.sr_ctx.mys_config.auto_game_sign
        self.auto_bbs_sign.value = self.sr_ctx.mys_config.auto_bbs_sign

        self.update()

    def _on_click_logout(self, e):
        """
        点击注销
        :param e:
        :return:
        """
        self.sr_ctx.mys_config.logout()
        self._update_login_related_components()
        msg = '注销成功'
        snack_bar.show_message(msg, self.flet_page)

    def _on_auto_game_sign_changed(self, e):
        self.sr_ctx.mys_config.auto_game_sign = self.auto_game_sign.value

    def _on_auto_bbs_sign_changed(self, e):
        self.sr_ctx.mys_config.auto_bbs_sign = self.auto_bbs_sign.value

    def _on_click_qrcode(self, e):
        """
        点击 显示二维码
        :param e:
        :return:
        """
        image = self.sr_ctx.mys_config.get_device_id_and_qrcode()
        if image is None:
            msg = '获取二维码失败'
            snack_bar.show_message(msg, self.flet_page)
            log.error(msg)
            return

        self.qrcode_img.src_base64 = image
        self.qrcode_img.visible = True
        self.qrcode_img.update()

        msg = '请使用米游社APP扫描二维码登录'
        snack_bar.show_message(msg, self.flet_page)
        log.info(msg)

        login = self.sr_ctx.mys_config.wait_qrcode_login()

        self.qrcode_img.visible = False
        self.qrcode_img.update()

        if login:
            self._update_login_related_components()


_settings_mys_view: Optional[SettingsMysView] = None


def get(page: ft.Page, ctx: Context) -> SettingsMysView:
    global _settings_mys_view
    if _settings_mys_view is None:
        _settings_mys_view = SettingsMysView(page, ctx)
    return _settings_mys_view

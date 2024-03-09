import webbrowser
from typing import Optional

import flet as ft

from basic.i18_utils import gt
from gui import components, snack_bar
from gui.sr_basic_view import SrBasicView
from sr.context import Context


class SettingsMysView(SrBasicView, ft.Row):

    def __init__(self, page: ft.Page, ctx: Context):
        SrBasicView.__init__(self, page, ctx)
        self.account_phone_text = ft.Text()
        self.logout_btn = components.RectOutlinedButton(gt('注销', 'ui'), on_click=self._on_click_logout)
        account_row_right = ft.Row(controls=[self.account_phone_text, self.logout_btn])

        self.auto_game_sign = ft.Checkbox(on_change=self._on_auto_game_sign_changed)
        self.auto_bbs_sign = ft.Checkbox(on_change=self._on_auto_bbs_sign_changed)

        setting_list = components.SettingsList(controls=[
            components.SettingsListItem(gt('账号状态', 'ui'), account_row_right),
            components.SettingsListItem(gt('自动游戏签到', 'ui'), self.auto_game_sign),
            components.SettingsListItem(gt('自动米游币任务', 'ui'), self.auto_bbs_sign),
        ])
        settings_card_title = components.CardTitleText(title=gt('米游社', 'ui'))
        settings_card = components.Card(setting_list, title=settings_card_title, width=400)

        self.phone_input: ft.TextField = ft.TextField(label=gt('电话号码', 'ui'), width=200)
        self.captcha_input: ft.TextField = ft.TextField(label=gt('验证码', 'ui'), width=200)
        self.captcha_btn = components.RectOutlinedButton(gt('获取验证码', 'ui'), on_click=self._on_click_captcha)
        self.login_btn = components.RectOutlinedButton(gt('登录', 'ui'), on_click=self._login)
        login_row = ft.Row(controls=[ft.Row(controls=[self.captcha_btn, self.login_btn])], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        login_card_content = ft.Column(controls=[self.phone_input, self.captcha_input, login_row])
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

        self.auto_game_sign.value = self.sr_ctx.mys_config.auto_game_sign
        self.auto_bbs_sign.value = self.sr_ctx.mys_config.auto_bbs_sign

        self.update()

    def _on_click_captcha(self, e):
        """
        尝试自动获取验证码 获取失败时打开浏览器
        使用默认浏览器，打开获取验证码的页面
        :param e:
        :return:
        """
        captcha_result: bool = self.sr_ctx.mys_config.try_captcha(self.phone_input.value)
        if captcha_result:
            msg = '自动获取验证码成功，请查收后填入'
        else:
            msg = '请从网页中触发获取验证码，但不要在网页中完成登录，回到脚本中输入验证码登录'
            webbrowser.open("https://user.mihoyo.com/#/login/captcha")
        snack_bar.show_message(msg, self.page)

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

    def _login(self, e):
        result = self.sr_ctx.mys_config.login(self.phone_input.value, self.captcha_input.value)
        msg = '登录成功' if result else '登录失败'
        snack_bar.show_message(msg, self.flet_page)
        self._update_login_related_components()

    def _on_auto_game_sign_changed(self, e):
        self.sr_ctx.mys_config.auto_game_sign = self.auto_game_sign.value

    def _on_auto_bbs_sign_changed(self, e):
        self.sr_ctx.mys_config.auto_bbs_sign = self.auto_bbs_sign.value


_settings_mys_view: Optional[SettingsMysView] = None


def get(page: ft.Page, ctx: Context) -> SettingsMysView:
    global _settings_mys_view
    if _settings_mys_view is None:
        _settings_mys_view = SettingsMysView(page, ctx)
    return _settings_mys_view

from typing import Optional

import flet as ft

from gui.sr_basic_view import SrBasicView
from sr.context import Context


class AccountListItem:

    def __init__(self):
        pass

class SettingsAccountView(ft.Row, SrBasicView):

    def __init__(self, page: ft.Page, ctx: Context):
        SrBasicView.__init__(self, page, ctx)




_settings_account_view: Optional[SettingsAccountView] = None


def get(page: ft.Page, ctx: Context) -> SettingsAccountView:
    global _settings_account_view
    if _settings_account_view is None:
        _settings_account_view = SettingsAccountView(page, ctx)

    return _settings_account_view

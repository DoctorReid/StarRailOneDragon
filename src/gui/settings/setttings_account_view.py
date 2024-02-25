from typing import Optional

import flet as ft
import re

from basic.i18_utils import gt
from gui.components import Card, SettingsList, SettingsListItem, SettingsListGroupTitle
from gui.settings import gui_config
from gui.settings.gui_config import ThemeColors
from gui.sr_basic_view import SrBasicView
from sr.sim_uni.sim_uni_challenge_config import load_all_challenge_config
from sr.app.sim_uni.sim_uni_config import get_sim_uni_app_config
from sr.context import Context
from sr.sim_uni.sim_uni_const import SimUniWorldEnum

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

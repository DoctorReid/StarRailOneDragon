import flet as ft
from typing import TypedDict, Optional, List

from sr.config import ConfigHolder


class GuiTheme:
    def __init__(self, cn: str, id: str):
        self.cn: str = cn
        self.id: str = id


GUI_THEME_LIGHT = GuiTheme(cn='正常模式', id='light')
GUI_THEME_DARK = GuiTheme(cn='深色模式', id='dark')
GUI_THEME_SYSTEM = GuiTheme(cn='跟随系统', id='system')

ALL_GUI_THEME_LIST: List[GuiTheme] = [GUI_THEME_LIGHT, GUI_THEME_DARK, GUI_THEME_SYSTEM]


class GuiConfig(ConfigHolder):

    def __init__(self):
        super().__init__('gui')
        self.system_theme: str = 'light'

    @property
    def theme_usage(self):
        config_theme = self.get('theme', 'system')
        if config_theme == 'system':
            return self.system_theme
        else:
            return config_theme

    @property
    def theme(self):
        return self.get('theme', 'system')

    @theme.setter
    def theme(self, value):
        self.update('theme', value)

    def init_system_theme(self, system_theme: str):
        """
        在应用启动时 初始化记录系统的主题
        :param system_theme:
        :return:
        """
        self.system_theme = system_theme


_gui_config: Optional[GuiConfig] = None


def get() -> GuiConfig:
    global _gui_config
    if _gui_config is None:
        _gui_config = GuiConfig()
    return _gui_config


class ThemeColors(TypedDict):
    window_bg: str
    component_bg: str
    divider_color: str
    progress_ring_color: str
    card_title_color: str
    success_icon_color: str
    fail_icon_color: str


light_theme = ThemeColors(
    window_bg='#F9F9F9',
    component_bg='#FFFFFF',
    divider_color='#C3C7CF',
    progress_ring_color='#D7E3F7',
    card_title_color=ft.colors.BLUE_300,
    success_icon_color=ft.colors.BLUE_300,
    fail_icon_color=ft.colors.RED
)

dark_theme = ThemeColors(
    window_bg='#080612',
    component_bg='#252331',
    divider_color='#888F8D',
    progress_ring_color='#D7E3F7',
    card_title_color=ft.colors.BLUE_300,
    success_icon_color=ft.colors.BLUE_300,
    fail_icon_color=ft.colors.RED
)


themes: dict[str, ThemeColors] = {
    'light': light_theme,
    'dark': dark_theme
}


def theme() -> ThemeColors:
    """
    获取对应主题的下的颜色
    :return:
    """
    return themes.get(_gui_config.theme_usage)

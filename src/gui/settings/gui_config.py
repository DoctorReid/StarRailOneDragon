from typing import TypedDict

from sr.config import ConfigHolder


class GuiConfig(ConfigHolder):

    def __init__(self):
        super().__init__('gui')

    @property
    def theme(self):
        return self.data.get('theme')

    @theme.setter
    def theme(self, value):
        self.data['theme'] = value
        self.write_config()


gc = GuiConfig()


class ThemeColors(TypedDict):
    window_bg: str
    component_bg: str
    divider_color: str
    progress_ring_color: str


light_theme = ThemeColors(
    window_bg='#F9F9F9',
    component_bg='#FFFFFF',
    divider_color='#C3C7CF',
    progress_ring_color='#D7E3F7'
)


themes: dict[str, ThemeColors] = {
    'light': light_theme
}


def theme() -> ThemeColors:
    """
    获取对应主题的下的颜色
    :return:
    """
    return themes.get(gc.theme)

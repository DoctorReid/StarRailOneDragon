from typing import Optional, List, Any, Callable

import flet as ft
from flet_core import OptionalNumber

from basic.i18_utils import gt
from gui.settings import gui_config
from gui.settings.gui_config import ThemeColors


class RectOutlinedButton(ft.OutlinedButton):

    def __init__(
            self,
            text: Optional[str] = None,
            icon: Optional[str] = None,
            visible: Optional[bool] = None,
            disabled: Optional[bool] = None,
            on_click=None,
            data: Any = None,
            width: OptionalNumber = None,
    ):
        style = ft.ButtonStyle(
            shape={
                ft.MaterialState.HOVERED: ft.RoundedRectangleBorder(radius=0),
                ft.MaterialState.DEFAULT: ft.RoundedRectangleBorder(radius=0),
            }
        )
        super().__init__(text=gt(text, 'ui'),
                         on_click=on_click,
                         data=data,
                         visible=visible,
                         disabled=disabled,
                         style=style,
                         width=width)


class CardTitleText(ft.Text):

    def __init__(self, title: str):
        theme: ThemeColors = gui_config.theme()
        super().__init__(title, size=20, weight=ft.FontWeight.W_600, color=theme['card_title_color'])

    def update_title(self, new_value: str):
        self.value = new_value
        self.update()


class Card(ft.Container):
    def __init__(self, content, title=None, width: int = 500, height: int = None):
        theme: ThemeColors = gui_config.theme()
        if title is not None:
            title_container = ft.Container(content=title, width=width, border=ft.border.only(bottom=ft.border.BorderSide(1, theme['divider_color'])))
            content_container = ft.Container(content=content, width=width, margin=ft.margin.only(top=5), expand=1)
            final_content = ft.Column(controls=[title_container, content_container], spacing=0, height=height)  # 如果一个Column里还要放Column 那外层需要固定高度
        else:
            final_content = content
        super().__init__(content=final_content,
                         border=ft.border.all(1, theme['divider_color']),
                         padding=5,
                         bgcolor=theme['component_bg'],
                         shadow=ft.BoxShadow(
                             spread_radius=1,
                             blur_radius=15,
                             color=ft.colors.GREY_300,
                             offset=ft.Offset(0, 0),
                             blur_style=ft.ShadowBlurStyle.OUTER,
                         )
                         )


class SettingsListItem(ft.Row):

    def __init__(self, label: str, value_component):
        super().__init__(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[ft.Text(label), value_component]
        )


class SettingsListGroupTitle(ft.Row):

    def __init__(self, title: str):
        super().__init__(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[CardTitleText(title)]
        )


class SettingsList(ft.ListView):

    def __init__(self,
                 controls: Optional[List[SettingsListItem]] = None,
                 width: Optional[int] = None):
        theme = gui_config.theme()
        container_list = []
        if controls is not None:
            for i in controls:
                container = ft.Container(
                    content=i,
                    border=ft.border.only(bottom=ft.border.BorderSide(1, theme['divider_color'])),
                    padding=10
                )
                container_list.append(container)
        super().__init__(
            controls=container_list,
            width=width
        )


class AfterDone(ft.Dropdown):

    def __init__(self, on_change: Optional[Callable] = None):
        super().__init__(options=[
            ft.dropdown.Option(key='none', text=gt('无', 'ui')),
            ft.dropdown.Option(key='shutdown', text=gt('关机', 'ui')),
            ft.dropdown.Option(key='close', text=gt('关游戏', 'ui'))
        ], label=gt('结束后'), value='none', on_change=on_change, width=200, text_size=14, height=50)

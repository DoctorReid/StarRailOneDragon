from typing import Optional

import flet as ft

from gui.settings import gui_config
from gui.settings.gui_config import ThemeColors


class RectOutlinedButton(ft.OutlinedButton):

    def __init__(
            self,
            text: Optional[str] = None,
            on_click=None,
            visible: Optional[bool] = None,
            disabled: Optional[bool] = None
    ):
        style = ft.ButtonStyle(
            shape={
                ft.MaterialState.HOVERED: ft.RoundedRectangleBorder(radius=0),
                ft.MaterialState.DEFAULT: ft.RoundedRectangleBorder(radius=0),
            }
        )
        super().__init__(text=text,
                         on_click=on_click,
                         visible=visible,
                         disabled=disabled,
                         style=style)


class CardTitleText(ft.Text):

    def __init__(self, title: str) :
        super().__init__(title, size=20, weight=ft.FontWeight.W_600, color=ft.colors.BLUE_300)


class Card(ft.Container):
    def __init__(self, content, title=None, width: int = 500):
        theme: ThemeColors = gui_config.theme()
        if title is not None:
            title_container = ft.Container(content=title, width=width, border=ft.border.only(bottom=ft.border.BorderSide(1, theme['divider_color'])))
            content_container = ft.Container(content=content, width=width, margin=ft.margin.only(top=5))
            final_content = ft.Column(controls=[title_container, content_container], spacing=0)
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

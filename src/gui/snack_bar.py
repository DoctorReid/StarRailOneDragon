import flet as ft


def show_message(msg: str, page: ft.Page):
    page.snack_bar = ft.SnackBar(ft.Text(msg))
    page.snack_bar.open = True
    page.update()

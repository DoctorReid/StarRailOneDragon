import flet as ft

from basic.i18_utils import gt
from sr.app.routine.assignments import Assignments
from sr.app.routine.email import Email
from sr.context import Context


class RoutineView:

    def __init__(self, page: ft.Page, ctx: Context):
        self.page = page
        self.ctx = ctx

        daily_text = ft.Text(value=gt('日常', 'ui'))
        self.assignment_btn = ft.ElevatedButton(text=gt('委托', 'ui'), on_click=self.run_assignment)
        self.email_btn = ft.ElevatedButton(text=gt('邮件', 'ui'), on_click=self.run_email)
        daily_row = ft.Row(controls=[
            self.assignment_btn,
            self.email_btn
        ])

        weekly_text = ft.Text(value=gt('周常', 'ui'))
        weekly_row = ft.Row(controls=[
        ])


        self.component = ft.Column(controls=[
            daily_text,
            daily_row,
            ft.Divider(),
            weekly_text
        ])

    def run_assignment(self, e):
        app = Assignments(self.ctx)
        app.execute()

    def run_email(self, e):
        app = Email(self.ctx)
        app.execute()


rv: RoutineView = None


def get(page: ft.Page, ctx: Context) -> RoutineView:
    global rv
    if rv is None:
        rv = RoutineView(page, ctx)
    return rv

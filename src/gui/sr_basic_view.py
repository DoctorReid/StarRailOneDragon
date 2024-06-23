from flet_core import Control
import flet as ft

from sr.context.context import Context


class SrBasicView(Control):

    def __init__(self, page: ft.Page, ctx: Context):
        self.flet_page: ft.Page = page
        self.sr_ctx: Context = ctx
        Control.__init__(self)

    def handle_after_show(self):
        """
        导航选择显示后的处理
        :return:
        """
        pass

    def handle_after_hide(self):
        """
        导航选择隐藏后的处理
        :return:
        """
        pass
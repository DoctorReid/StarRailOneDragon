from PySide6.QtWidgets import QWidget
from qfluentwidgets import HyperlinkCard, FluentIcon
from typing import Optional

from one_dragon.base.operation.application_base import Application
from one_dragon.gui.component.column_widget import ColumnWidget
from one_dragon.gui.view.app_run_interface import AppRunInterface
from sr_od.app.sim_uni.sim_uni_app import SimUniApp
from sr_od.app.sr_application import SrApplication
from sr_od.context.sr_context import SrContext


class SimUniRunInterface(AppRunInterface):

    def __init__(self,
                 ctx: SrContext,
                 parent=None):
        self.ctx: SrContext = ctx
        self.app: Optional[SrApplication] = None

        AppRunInterface.__init__(
            self,
            ctx=ctx,
            object_name='sr_sim_uni_run_interface',
            nav_text_cn='运行',
            parent=parent,
        )

    def get_widget_at_top(self) -> QWidget:
        content = ColumnWidget()

        self.help_opt = HyperlinkCard(icon=FluentIcon.HELP, title='使用说明', text='前往', content='先看说明 再使用与提问',
                                      url='https://one-dragon.org/sr/zh/docs/feat_sim_uni.html')
        content.add_widget(self.help_opt)

        return content

    def get_app(self) -> Application:
        return SimUniApp(self.ctx)

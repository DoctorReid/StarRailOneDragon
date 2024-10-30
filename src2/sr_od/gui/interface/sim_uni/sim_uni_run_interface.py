from PySide6.QtWidgets import QWidget
from typing import Optional

from one_dragon.base.operation.application_base import Application
from one_dragon.gui.component.row_widget import RowWidget
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
        content = RowWidget()

        return content

    def get_app(self) -> Application:
        return SimUniApp(self.ctx)

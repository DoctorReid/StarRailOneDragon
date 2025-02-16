from PySide6.QtWidgets import QWidget
from qfluentwidgets import HyperlinkCard, FluentIcon
from typing import Optional

from one_dragon.base.operation.application_base import Application
from one_dragon_qt.widgets.column import Column
from one_dragon_qt.view.app_run_interface import AppRunInterface
from sr_od.app.sr_application import SrApplication
from sr_od.app.world_patrol.world_patrol_app import WorldPatrolApp
from sr_od.context.sr_context import SrContext


class WorldPatrolRunInterface(AppRunInterface):

    def __init__(self,
                 ctx: SrContext,
                 parent=None):
        self.ctx: SrContext = ctx
        self.app: Optional[SrApplication] = None

        AppRunInterface.__init__(
            self,
            ctx=ctx,
            object_name='sr_world_patrol_run_interface',
            nav_text_cn='运行',
            parent=parent,
        )

    def get_widget_at_top(self) -> QWidget:
        content = Column()

        self.help_opt = HyperlinkCard(icon=FluentIcon.HELP, title='使用说明', text='前往', content='先看说明 再使用与提问',
                                      url='https://onedragon-anything.github.io/sr/zh/docs/feat_world_patrol.html')
        content.add_widget(self.help_opt)

        return content

    def get_app(self) -> Application:
        return WorldPatrolApp(self.ctx)

from qfluentwidgets import FluentIcon

from one_dragon_qt.widgets.pivot_navi_interface import PivotNavigatorInterface
from sr_od.context.sr_context import SrContext
from sr_od.gui.interface.game_assistant.calibrator_run_interface import CalibratorRunInterface


class GameAssistantInterface(PivotNavigatorInterface):

    def __init__(self, ctx: SrContext, parent=None):
        self.ctx: SrContext = ctx
        PivotNavigatorInterface.__init__(self, object_name='sr_game_assistant_interface', parent=parent,
                                         nav_text_cn='游戏助手', nav_icon=FluentIcon.GAME)

    def create_sub_interface(self):
        """
        创建下面的子页面
        :return:
        """
        self.add_sub_interface(CalibratorRunInterface(ctx=self.ctx))

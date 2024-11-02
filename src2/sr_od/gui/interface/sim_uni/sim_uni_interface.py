from qfluentwidgets import FluentIcon

from one_dragon.gui.component.interface.pivot_navi_interface import PivotNavigatorInterface
from sr_od.context.sr_context import SrContext
from sr_od.gui.interface.sim_uni.sim_uni_challenge_config_interface import SimUniChallengeConfigInterface
from sr_od.gui.interface.sim_uni.sim_uni_run_interface import SimUniRunInterface


class SimUniInterface(PivotNavigatorInterface):

    def __init__(self, ctx: SrContext, parent=None):
        self.ctx: SrContext = ctx
        PivotNavigatorInterface.__init__(self, object_name='sr_sim_uni_interface', parent=parent,
                                         nav_text_cn='模拟宇宙', nav_icon=FluentIcon.IOT)

    def create_sub_interface(self):
        """
        创建下面的子页面
        :return:
        """
        self.add_sub_interface(SimUniRunInterface(self.ctx))
        self.add_sub_interface(SimUniChallengeConfigInterface(self.ctx))
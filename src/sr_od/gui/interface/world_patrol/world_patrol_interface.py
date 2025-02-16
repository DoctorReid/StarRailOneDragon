from qfluentwidgets import FluentIcon

from one_dragon_qt.widgets.pivot_navi_interface import PivotNavigatorInterface
from sr_od.context.sr_context import SrContext
from sr_od.gui.interface.world_patrol.world_patrol_draw_route_interface import WorldPatrolDrawRouteInterface
from sr_od.gui.interface.world_patrol.world_patrol_run_interface import WorldPatrolRunInterface
from sr_od.gui.interface.world_patrol.world_patrol_setting_interface import WorldPatrolSettingInterface
from sr_od.gui.interface.world_patrol.world_patrol_whitelist_interface import WorldPatrolWhitelistInterface


class WorldPatrolInterface(PivotNavigatorInterface):

    def __init__(self, ctx: SrContext, parent=None):
        self.ctx: SrContext = ctx
        PivotNavigatorInterface.__init__(self, object_name='sr_world_patrol_interface', parent=parent,
                                         nav_text_cn='锄大地', nav_icon=FluentIcon.ROTATE)

    def create_sub_interface(self):
        """
        创建下面的子页面
        :return:
        """
        self.add_sub_interface(WorldPatrolRunInterface(ctx=self.ctx))
        self.add_sub_interface(WorldPatrolSettingInterface(ctx=self.ctx))
        self.add_sub_interface(WorldPatrolWhitelistInterface(ctx=self.ctx))
        self.add_sub_interface(WorldPatrolDrawRouteInterface(ctx=self.ctx))

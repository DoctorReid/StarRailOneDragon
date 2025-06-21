from qfluentwidgets import FluentIcon

from one_dragon_qt.widgets.pivot_navi_interface import PivotNavigatorInterface
from sr_od.context.sr_context import SrContext
from sr_od.gui.interface.setting.sr_setting_instance_interface import SrSettingInstanceInterface


class AccountsInterface(PivotNavigatorInterface):

    def __init__(self,
                 ctx: SrContext,
                 parent=None):
        self.ctx: SrContext = ctx
        PivotNavigatorInterface.__init__(self, object_name='app_accounts_interface', parent=parent,
                                         nav_text_cn='账户管理', nav_icon=FluentIcon.COPY)

    def create_sub_interface(self):
        """
        创建下面的子页面
        :return:
        """
        self.add_sub_interface(SrSettingInstanceInterface(ctx=self.ctx))

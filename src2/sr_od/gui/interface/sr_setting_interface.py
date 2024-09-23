from qfluentwidgets import FluentIcon

from one_dragon.gui.component.interface.pivot_navi_interface import PivotNavigatorInterface
from one_dragon.gui.view.setting.setting_env_interface import SettingEnvInterface
from one_dragon.gui.view.setting.setting_instance_interface import SettingInstanceInterface
from sr_od.context.sr_context import SrContext
from sr_od.gui.interface.sr_setting_game_interface import SrSettingGameInterface


class SrSettingInterface(PivotNavigatorInterface):

    def __init__(self, ctx: SrContext, parent=None):
        self.ctx: SrContext = ctx
        PivotNavigatorInterface.__init__(self, object_name='sr_setting_interface', parent=parent,
                                         nav_text_cn='设置', nav_icon=FluentIcon.SETTING)

    def create_sub_interface(self):
        """
        创建下面的子页面
        :return:
        """
        self.add_sub_interface(SrSettingGameInterface(ctx=self.ctx))
        self.add_sub_interface(SettingEnvInterface(ctx=self.ctx))
        self.add_sub_interface(SettingInstanceInterface(ctx=self.ctx))

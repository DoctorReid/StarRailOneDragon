import sys

from PySide6.QtWidgets import QApplication
from qfluentwidgets import NavigationItemPosition, Theme, setTheme

from one_dragon.base.operation.one_dragon_env_context import OneDragonEnvContext
from one_dragon_qt.app.installer import InstallerWindowBase
from one_dragon_qt.view.code_interface import CodeInterface
from one_dragon_qt.view.install_interface import InstallerInterface
from one_dragon_qt.view.installer_setting_interface import InstallerSettingInterface
from one_dragon.utils.i18_utils import gt


class SrInstallerWindow(InstallerWindowBase):

    def __init__(self, ctx: OneDragonEnvContext, win_title: str, parent=None):
        InstallerWindowBase.__init__(
            self,
            ctx=ctx,
            win_title=win_title,
            parent=parent,
            app_icon='installer_app.ico'
        )

    def create_sub_interface(self):
        self.add_sub_interface(InstallerInterface(self.ctx, parent=self))
        self.add_sub_interface(CodeInterface(self.ctx, parent=self), position=NavigationItemPosition.BOTTOM)
        self.add_sub_interface(InstallerSettingInterface(self.ctx, parent=self), position=NavigationItemPosition.BOTTOM)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    _ctx = OneDragonEnvContext()
    setTheme(Theme[_ctx.env_config.theme.upper()])
    w = SrInstallerWindow(_ctx, gt(f'{_ctx.project_config.project_name}-installer', 'ui'))
    w.show()
    app.exec()

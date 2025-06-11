from one_dragon.launcher.application_launcher import ApplicationLauncher
from sr_od.app.sr_one_dragon_app import SrOneDragonApp
from sr_od.context.sr_context import SrContext


class SrApplicationLauncher(ApplicationLauncher):
    """星铁应用启动器"""

    def create_context(self):
        return SrContext()

    def get_app_class(self):
        return SrOneDragonApp


if __name__ == '__main__':
    launcher = SrApplicationLauncher()
    launcher.run()
from basic.i18_utils import gt
from gui import components
from sr.context import Context


class OneStopServiceSettingsView:

    def __init__(self, ctx: Context):
        self.ctx: Context = ctx

        task_title = components.CardTitleText(gt('执行频率', 'ui'))

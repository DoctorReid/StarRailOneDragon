from basic.i18_utils import gt
from gui import components
from gui.sr_basic_view import SrBasicView
from sr.context import Context


class SettingsTrailblazePowerView(SrBasicView):

    def __init__(self, ctx: Context):
        plan_title = components.CardTitleText(gt('体力规划', 'ui'))

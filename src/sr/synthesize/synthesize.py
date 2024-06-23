from basic.i18_utils import gt
from sr.context.context import Context
from sr.operation import StateOperation


class Synthesize(StateOperation):

    def __init__(self, ctx: Context):
        """
        如果不在合成页面 则进入合成页面
        合成指定物品后 停留在指定页面
        :param ctx:
        """
        super().__init__(ctx, try_times=5,
                         op_name='%s %s' % (gt('合成', 'ui')))
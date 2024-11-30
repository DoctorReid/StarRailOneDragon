from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from sr_od.app.sr_application import SrApplication
from sr_od.context.sr_context import SrContext
from sr_od.operations.back_to_normal_world_plus import BackToNormalWorldPlus


class RelicSalvageApp(SrApplication):

    def __init__(self, ctx: SrContext):
        SrApplication.__init__(self, ctx, 'relic_salvage', op_name=gt('遗器分解', 'ui'),
                               run_record=ctx.relic_salvage_run_record)

    @operation_node(name='开始前返回', is_start_node=True)
    def back_at_first(self) -> OperationRoundResult:
        op = BackToNormalWorldPlus(self.ctx)
        return self.round_by_op_result(op.execute())

    @node_from(from_name='开始前返回')
    @operation_node(name='前往分解画面')
    def goto_salvage(self) -> OperationRoundResult:
        return self.round_by_goto_screen(screen_name='背包-遗器', retry_wait=1)


def __debug():
    ctx = SrContext()
    ctx.init_by_config()
    app = RelicSalvageApp(ctx)
    app.execute()


if __name__ == '__main__':
    __debug()
from typing import List

from sr.app.application_base import Application
from sr.context import Context
from sr.operation import Operation, StateOperationEdge, StateOperationNode, OperationOneRoundResult
from sr.operation.common.back_to_normal_world_plus import BackToNormalWorldPlus
from sr.operation.unit.enter_game import LoginWithAnotherAccount


class SwitchAccountApp(Application):

    def __init__(self, ctx: Context, target_account_idx: int):
        edges: List[StateOperationEdge] = []

        world = StateOperationNode('返回大世界', op=BackToNormalWorldPlus(ctx))
        switch = StateOperationNode('切换账号', self._switch)
        edges.append(StateOperationEdge(world, switch))

        super().__init__(ctx,
                         op_name='切换账号',
                         edges=edges
                         )

        self.target_account_idx: int = target_account_idx

    def _switch(self) -> OperationOneRoundResult:
        self.ctx.active_account(self.target_account_idx)
        op = LoginWithAnotherAccount(self.ctx)
        return Operation.round_by_op(op.execute())

from typing import Optional, List, ClassVar

from basic import Point
from basic.i18_utils import gt
from sr.const.map_const import get_sp_by_cn, region_with_another_floor
from sr.context.context import Context, get_context
from sr.custom_combine_op.custom_combine_op_config import CustomCombineOpConfig, CustomCombineOpItem
from sr.custom_combine_op.custom_combine_op_const import OpEnum, OpWaitTypeEnum, OpInteractTypeEnum
from sr.operation import StateOperation, OperationOneRoundResult, Operation, OperationFail, StateOperationNode
from sr.operation.combine.transport import Transport
from sr.operation.common.back_to_normal_world_plus import BackToNormalWorldPlus
from sr.operation.unit.click import ClickPoint
from sr.operation.unit.interact import Interact, TalkInteract
from sr.operation.unit.move import MoveDirectly
from sr.operation.unit.store.buy_store_item_2 import BuyStoreItem2
from sr.operation.unit.store.store_const import StoreItemEnum
from sr.operation.unit.wait import WaitInWorld, WaitInSeconds


class CustomCombineOp(StateOperation):

    STATUS_ALL_DONE: ClassVar[str] = '全部完成'

    def __init__(self, ctx: Context, config_name: str):
        """
        按配置文件执行对应的指令
        最后会返回大世界
        :param ctx:
        :param config_name:
        """
        self.config: CustomCombineOpConfig = CustomCombineOpConfig(config_name)

        super().__init__(ctx, op_name=gt(self.config.config_name, 'ui'))

    def handle_init(self) -> Optional[OperationOneRoundResult]:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        可以返回初始化后判断的结果
        - 成功时跳过本指令
        - 失败时立刻返回失败
        - 不返回时正常运行本指令
        """
        if not self.config.existed:
            return self.round_fail('配置文件不存在')

        self.op_idx: int = 0  # 当前指定的指令下标

        return None

    def add_edges_and_nodes(self) -> None:
        """
        初始化前 添加边和节点 由子类实行
        :return:
        """
        run_op = StateOperationNode('执行指令', self.run_op)
        self.add_edge(run_op, run_op)  # 循环执行指令

        finish = StateOperationNode('返回', self.finish)
        self.add_edge(run_op, finish, status=CustomCombineOp.STATUS_ALL_DONE)

        self.param_start_node = run_op

    def run_op(self) -> OperationOneRoundResult:
        op_item: CustomCombineOpItem = self.config.ops[self.op_idx]
        next_op_item: CustomCombineOpItem = None if self.op_idx >= len(self.config.ops) - 1 else self.config.ops[self.op_idx + 1]

        if op_item.op == OpEnum.BACK_TO_WORLD_PLUS.value:
            op = BackToNormalWorldPlus(self.ctx)
        elif op_item.op == OpEnum.TRANSPORT.value:
            op = self.op_transport(op_item)
        elif op_item.op == OpEnum.WAIT.value:
            op = self.op_wait(op_item)
        elif op_item.op in [OpEnum.MOVE.value, OpEnum.SLOW_MOVE.value]:
            op = self.op_move(op_item, next_op_item)
        elif op_item.op == OpEnum.INTERACT.value:
            op = self.op_interact(op_item)
        elif op_item.op == OpEnum.CLICK.value:
            op = ClickPoint(self.ctx, Point(int(op_item.data[0]), int(op_item.data[1])))
        elif op_item.op == OpEnum.BUY_STORE_ITEM.value:
            op = self.op_buy_store_item(op_item)
        else:
            return self.round_fail(f'不支持的指令 {op_item.op}')

        op_result = op.execute()
        if op_result.success or op_item:
            self.op_idx += 1
            if self.op_idx >= len(self.config.ops):
                return self.round_success(CustomCombineOp.STATUS_ALL_DONE)
            else:
                return self.round_success()
        else:
            return self.round_by_op(op_result)

    def op_transport(self, op_item: CustomCombineOpItem) -> Operation:
        """
        传送指令
        :param op_item:
        :return:
        """
        planet_name = op_item.data[0]
        region_name = op_item.data[1]
        region_floor = int(op_item.data[2])
        tp_name = op_item.data[3]

        tp = get_sp_by_cn(planet_name, region_name, region_floor, tp_name)

        return Transport(self.ctx, tp)

    def op_wait(self, op_item: CustomCombineOpItem) -> Operation:
        """
        等待指令
        :param op_item:
        :return:
        """
        wait_type = op_item.data[0]
        wait_seconds = float(op_item.data[1])
        if wait_type == OpWaitTypeEnum.IN_WORLD.value:
            return WaitInWorld(self.ctx, wait_seconds)
        elif wait_type == OpWaitTypeEnum.SECONDS.value:
            return WaitInSeconds(self.ctx, wait_seconds)
        else:
            return OperationFail(self.ctx, status='错误的等待类型 %s' % wait_type)

    def op_move(self, op_item: CustomCombineOpItem, next_op_item: CustomCombineOpItem):
        """
        移动指令
        :param op_item:
        :param next_op_item:
        :return:
        """
        data: List[int] = [int(i) for i in op_item.data]
        current_pos = self.ctx.pos_point
        current_lm_info = self.ctx.ih.get_large_map(self.ctx.pos_region)

        if len(data) > 2:
            next_region = region_with_another_floor(self.ctx.pos_region, data[2])
            next_lm_info = self.ctx.ih.get_large_map(next_region)
        else:
            next_region = None
            next_lm_info = None
        next_pos = Point(data[0], data[1])

        # 看后续指令判断这次移动结束后要不要停止
        dont_stop_afterwards = (
                next_op_item is not None and
                next_op_item.op in [
                    OpEnum.MOVE.value,
                    OpEnum.SLOW_MOVE.value,
                    OpEnum.PATROL.value,  # 如果下一个是攻击 则靠攻击停止移动 这样还可以取消疾跑后摇
                ]
        )

        no_run = op_item.op == OpEnum.SLOW_MOVE.value

        return MoveDirectly(self.ctx, current_lm_info, next_lm_info=next_lm_info,
                            target=next_pos, start=current_pos,
                            stop_afterwards=not dont_stop_afterwards, no_run=no_run,
                            technique_fight=self.ctx.world_patrol_config.technique_fight,
                            technique_only=self.ctx.world_patrol_config.technique_only
                            )

    def op_interact(self, op_item: CustomCombineOpItem) -> Operation:
        """
        交互指令
        :param op_item:
        :return:
        """
        interact_type = op_item.data[0]
        interact_word = op_item.data[1]
        interact_lcs_percent = float(op_item.data[2]) if len(op_item.data) > 2 else 0.5
        interact_single_line = interact_type in [OpInteractTypeEnum.WORLD_SINGLE_LINE.value]

        if interact_type in [OpInteractTypeEnum.WORLD.value, OpInteractTypeEnum.WORLD_SINGLE_LINE.value]:
            return Interact(self.ctx, cn=interact_word,
                            lcs_percent=interact_lcs_percent,
                            single_line=interact_single_line)
        elif interact_type == OpInteractTypeEnum.TALK.value:
            return TalkInteract(self.ctx, option=interact_word, lcs_percent=interact_lcs_percent)
        else:
            return OperationFail(self.ctx, status='错误的交互类型 %s' % interact_type)

    def op_buy_store_item(self, op_item: CustomCombineOpItem) -> Operation:
        """
        购买商品指令
        :param op_item:
        :return:
        """
        item_id = op_item.data[0]
        buy_num = int(op_item.data[1])
        store_item = StoreItemEnum[item_id.upper()].value

        return BuyStoreItem2(self.ctx, store_item, buy_num)

    def finish(self) -> OperationOneRoundResult:
        """
        完成指令结束
        :return:
        """
        op = BackToNormalWorldPlus(self.ctx)
        return self.round_by_op(op.execute())


def __debug_op():
    ctx = get_context()
    ctx.start_running()

    op = CustomCombineOp(ctx, 'buy_trick_snack')
    op.execute()


if __name__ == '__main__':
    __debug_op()
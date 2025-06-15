import time

from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from sr_od.context.sr_context import SrContext
from sr_od.operations.sr_operation import SrOperation


class DivUniChooseCurio(SrOperation):

    def __init__(self, ctx: SrContext, skip_initial_screen_check: bool = False):
        """
        选择奇物 点击一次确认后退出
        """
        SrOperation.__init__(self, ctx, op_name=gt('差分宇宙-选择奇物', 'ui'))
        self.skip_initial_screen_check: bool = skip_initial_screen_check  # 是否跳过初始画面识别

    @operation_node(name='识别初始画面', is_start_node=True)
    def check_initial_screen(self) -> OperationRoundResult:
        if self.skip_initial_screen_check:
            return self.round_success()
        screen = self.screenshot()
        current_screen_name: str = self.check_and_update_current_screen(
            screen,
            [
                '差分宇宙-选择奇物'
            ]
        )

        if current_screen_name is None:
            return self.round_retry(status='未能识别当前画面', wait=1)
        else:
            return self.round_success(status=current_screen_name)

    @node_from(from_name='识别初始画面')
    @operation_node(name='处理选择奇物')
    def handle_choose(self) -> OperationRoundResult:
        screen = self.screenshot()

        curio_pos_list = self.ctx.div_uni_context.get_curio_pos(screen)
        # 暂时没有看到刷新按钮
        to_choose_list = self.ctx.div_uni_context.get_reward_by_priority(
            reward_list=curio_pos_list,
            choose_num=1,
            consider_priority_1=True,
            consider_priority_2=True,
            consider_priority_new=True,
            consider_not_in_priority=True,
            ignore_idx_list=None,
        )

        if len(to_choose_list) > 0:
            for to_choose in to_choose_list:
                self.ctx.controller.click(to_choose.rect.center)
                time.sleep(0.5)

            return self.round_by_ocr_and_click(screen, '确认', lcs_percent=1, retry_wait=1)
        else:
            return self.round_retry(status='按优先级未匹配到奇物', wait=1)


def __debug():
    ctx = SrContext()
    ctx.ocr.init_model()
    ctx.init_by_config()
    ctx.div_uni_context.init_for_div_uni()
    ctx.start_running()

    op = DivUniChooseCurio(ctx)
    op.execute()


if __name__ == '__main__':
    __debug()
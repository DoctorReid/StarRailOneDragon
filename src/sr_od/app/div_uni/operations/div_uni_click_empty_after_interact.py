import time

from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from sr_od.context.sr_context import SrContext
from sr_od.operations.sr_operation import SrOperation


class DivUniClickEmptyAfterInteract(SrOperation):

    def __init__(self, ctx: SrContext, skip_initial_screen_check: bool = False):
        """
        点击一次空白处后退出
        """
        SrOperation.__init__(self, ctx, op_name=gt('差分宇宙-交互后点击空白', 'ui'))
        self.skip_initial_screen_check: bool = skip_initial_screen_check  # 是否跳过初始画面识别

    @operation_node(name='识别初始画面', is_start_node=True)
    def check_initial_screen(self) -> OperationRoundResult:
        if self.skip_initial_screen_check:
            return self.round_success()
        screen = self.screenshot()
        current_screen_name: str = self.check_and_update_current_screen(
            screen,
            [
                '模拟宇宙-获得物品',
                '模拟宇宙-获得奇物',
                '模拟宇宙-获得祝福',
                '差分宇宙-获得方程',
            ]
        )

        if current_screen_name is None:
            return self.round_retry(status='未能识别当前画面', wait=1)
        else:
            return self.round_success(status=current_screen_name)

    @node_from(from_name='识别初始画面')
    @operation_node(name='处理点击空白')
    def handle_click_empty(self) -> OperationRoundResult:
        screen = self.screenshot()

        return self.round_by_ocr_and_click(screen, '点击空白处关闭',
                                           success_wait=1, retry_wait=1)


def __debug():
    ctx = SrContext()
    ctx.ocr.init_model()
    ctx.init_by_config()
    ctx.div_uni_context.init_for_div_uni()
    ctx.start_running()

    op = DivUniClickEmptyAfterInteract(ctx)
    op.execute()


if __name__ == '__main__':
    __debug()
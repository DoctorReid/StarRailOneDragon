from typing import Optional

from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from sr_od.app.div_uni.operations.div_uni_choose_bless import DivUniChooseBless
from sr_od.app.div_uni.operations.div_uni_choose_curio import DivUniChooseCurio
from sr_od.app.div_uni.operations.div_uni_click_empty_after_interact import DivUniClickEmptyAfterInteract
from sr_od.context.sr_context import SrContext
from sr_od.operations.sr_operation import SrOperation


class DivUniHandleNotInWorld(SrOperation):

    def __init__(
            self,
            ctx: SrContext,
    ):
        """
        处理非大世界画面
        识别到大世界画面则尽快返回 防止被怪袭击
        """
        SrOperation.__init__(self, ctx, op_name=gt('差分宇宙-非大世界处理', 'ui'))

        self.last_know_screen_time: float = 0  # 上一次可识别画面的时间


    @operation_node(name='识别初始画面', is_start_node=True, node_max_retry_times=9999)
    def handle_not_in_normal_world(self) -> OperationRoundResult:
        self.ctx.detect_info.view_down = False  # 进入了非大世界画面 就将视角重置
        screen = self.screenshot()

        op: Optional[SrOperation] = None
        current_screen_name: str = self.ctx.div_uni_context.check_screen_name(screen)
        if current_screen_name is None:
            return self.round_retry(status='未识别', wait_round_time=0.1)
        elif current_screen_name in ['模拟宇宙-获得物品', '模拟宇宙-获得奇物', '差分宇宙-获得方程', '模拟宇宙-获得祝福',]:
            op = DivUniClickEmptyAfterInteract(self.ctx, skip_initial_screen_check=True)
        elif current_screen_name == '差分宇宙-选择奇物':
            op = DivUniChooseCurio(self.ctx, skip_initial_screen_check=True)
        elif current_screen_name == '差分宇宙-选择祝福':
            op = DivUniChooseBless(self.ctx, skip_initial_screen_check=True)
        elif current_screen_name == '差分宇宙-大世界':
            return self.round_success(current_screen_name)

        if op is not None:
            op_result = op.execute()
            if op_result.success:
                return self.round_wait(status=op_result.status)
            else:
                return self.round_retry(status=op_result.status, wait=1)

        return self.round_success(status='处理完成')


def __debug():
    ctx = SrContext()
    ctx.ocr.init_model()
    ctx.init_by_config()
    ctx.div_uni_context.init_for_div_uni()
    ctx.start_running()

    op = DivUniHandleNotInWorld(ctx)
    op.execute()


if __name__ == '__main__':
    __debug()
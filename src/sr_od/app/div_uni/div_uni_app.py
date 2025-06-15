from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from sr_od.app.div_uni.div_uni_run_level import DivUniRunLevel
from sr_od.app.sr_application import SrApplication
from sr_od.context.sr_context import SrContext
from sr_od.interastral_peace_guide.guide_transport import GuideTransport


class DivUniApp(SrApplication):

    def __init__(self, ctx: SrContext):
        """
        差分宇宙应用 需要在大世界中非战斗、非特殊关卡界面中开启
        :param ctx:
        """
        SrApplication.__init__(self, ctx, 'divergent_universe',
                               op_name=gt('差分宇宙', 'ui'),
                               run_record=ctx.sim_uni_record)

    @operation_node(name='检查运行次数', is_start_node=True)
    def check_times(self) -> OperationRoundResult:
        return self.round_success()

    @node_from(from_name='检查运行次数')
    @operation_node(name='识别初始画面')
    def check_initial_screen(self) -> OperationRoundResult:
        screen = self.screenshot()
        current_screen_name: str = self.check_and_update_current_screen(
            screen,
            [
                '差分宇宙-入口',
                '差分宇宙-选择奇物',
            ]
        )
        if current_screen_name is not None:
            return self.round_success(status=current_screen_name)
        else:
            return self.round_success(status='未知画面')

    @node_from(from_name='识别初始画面', status='未知画面')
    @node_from(from_name='识别初始画面', status='差分宇宙-入口')
    @operation_node(name='传送')
    def transport(self) -> OperationRoundResult:
        tab = self.ctx.guide_data.best_match_tab_by_name(gt('模拟宇宙'))
        category = self.ctx.guide_data.best_match_category_by_name(gt('差分宇宙'), tab)
        mission = self.ctx.guide_data.best_match_mission_by_name('奖励预览', category)
        op = GuideTransport(self.ctx, mission)
        return self.round_by_op_result(op.execute())

    @node_from(from_name='识别初始画面', status='差分宇宙-入口')
    @node_from(from_name='传送')
    @operation_node(name='处理入口画面', node_max_retry_times=10)
    def handle_entry_screen(self) -> OperationRoundResult:
        screen = self.screenshot()
        current_screen_name: str = self.check_and_update_current_screen(screen, ['差分宇宙-入口'])
        if current_screen_name is None:
            return self.round_retry(status='等待差分宇宙入口画面加载', wait=1)

        return self.round_by_find_and_click_area(screen, '差分宇宙-入口', '按钮-开始游戏',
                                                 success_wait=3, retry_wait=1)

    @node_from(from_name='处理入口画面')
    @operation_node(name='模式选择')
    def handle_choose_mode(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_ocr_and_click(screen, '周期验算', success_wait=1, retry_wait=1)

    @node_from(from_name='模式选择')
    @operation_node(name='启动差分宇宙')
    def handle_start(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_ocr_and_click(screen, '启动「差分宇宙」', success_wait=1, retry_wait=1)

    @node_from(from_name='启动差分宇宙')
    @operation_node(name='差分宇宙初始化')
    def init_for_div_uni(self) -> OperationRoundResult:
        self.ctx.div_uni_context.init_for_div_uni()
        return self.round_success()

    @node_from(from_name='识别初始画面', status='差分宇宙-选择奇物')
    @node_from(from_name='差分宇宙初始化')
    @operation_node(name='层间移动')
    def run_level(self) -> OperationRoundResult:
        op = DivUniRunLevel(self.ctx)
        return self.round_by_op_result(op.execute())


def __debug():
    ctx = SrContext()
    ctx.init_by_config()
    ctx.init_for_sim_uni()
    ctx.start_running()
    op = DivUniApp(ctx)
    op.execute()


if __name__ == '__main__':
    __debug()
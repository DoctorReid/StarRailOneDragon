from typing import List, ClassVar

from basic.i18_utils import gt
from sr.context.context import Context
from sr.image.sceenshot import screen_state
from sr.operation import StateOperation, StateOperationEdge, OperationOneRoundResult, Operation, StateOperationNode
from sr.operation.common.back_to_normal_world_plus import BackToNormalWorldPlus
from sr.screen_area.screen_missions import ScreenMission
from sr.screen_area.screen_normal_world import ScreenNormalWorld


class CancelMissionTrace(StateOperation):

    STATUS_CANCELLED: ClassVar[str] = '已取消'
    STATUS_CLICK_TRACE: ClassVar[str] = '尝试点击追踪任务'

    def __init__(self, ctx: Context):
        """
        尝试取消任务追踪 在需要使用大地图的app启动时调用
        :param ctx:
        """
        edges: List[StateOperationEdge] = []

        open_mission = StateOperationNode('点击追踪任务', self._try_open_mission)

        # 之前还没有取消过 进行尝试
        cancel_trace = StateOperationNode('取消追踪', self._cancel_trace)
        edges.append(StateOperationEdge(open_mission, cancel_trace, status=CancelMissionTrace.STATUS_CLICK_TRACE))

        # 点击取消之后 返回大世界
        back = StateOperationNode('返回大世界', op=BackToNormalWorldPlus(ctx))
        edges.append(StateOperationEdge(cancel_trace, back, status=CancelMissionTrace.STATUS_CANCELLED))

        # 点击失败的情况 也兜底返回大世界 不卡死后续操作
        edges.append(StateOperationEdge(cancel_trace, back, success=False))

        super().__init__(ctx, op_name=gt('取消任务追踪', 'ui'),
                         edges=edges)

        self.in_world_times: int = 0  # 判断在大世界的次数

    def _try_open_mission(self) -> OperationOneRoundResult:
        """
        有任务追踪时 左方有一个当前追踪的显示
        尝试点击左方这个任务唤出任务列表
        :return:
        """
        if self.ctx.pos_cancel_mission_trace:
            return self.round_success()

        area = ScreenNormalWorld.TRACE_MISSION_ICON.value
        if self.ctx.controller.click(area.center, pc_alt=True):
            return self.round_success(CancelMissionTrace.STATUS_CLICK_TRACE, wait=1)
        else:
            return self.round_retry('点击任务图标失败', wait=1)

    def _cancel_trace(self) -> OperationOneRoundResult:
        """
        根据当前屏幕状态 尝试取消追踪
        :return:
        """
        screen = self.screenshot()
        if screen_state.is_normal_in_world(screen, self.ctx.im):  # 依旧在大地图 说明没有追踪任务
            self.ctx.pos_cancel_mission_trace = True
            return self.round_success()

        area1 = ScreenMission.CANCEL_TRACE_BTN.value
        click = self.find_and_click_area(area1, screen)
        if click == Operation.OCR_CLICK_SUCCESS:
            self.ctx.pos_cancel_mission_trace = True
            return self.round_success(CancelMissionTrace.STATUS_CANCELLED)
        else:
            return self.round_retry('点击%s失败' % area1.status, wait=1)

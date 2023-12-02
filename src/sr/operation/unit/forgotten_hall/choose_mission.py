import time

from cv2.typing import MatLike, Point

from basic.i18_utils import gt
from basic.img import MatchResult
from sr.context import Context
from sr.operation import Operation, OperationOneRoundResult
from sr.operation.unit.forgotten_hall import get_mission_num_pos, CHOOSE_MISSION_RECT


class ChooseMission(Operation):

    def __init__(self, ctx: Context, mission_num: int):
        """
        根据关卡数字 点击对应的关卡
        :param ctx: 应用上下文
        :param mission_num: 选择哪个关卡 1~10
        """
        super().__init__(ctx, try_times=5, op_name='%s %d' % (gt('忘却之庭选择关卡', 'ui'), mission_num))
        self.mission_num: int = mission_num

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen: MatLike = self.screenshot()

        num_result: MatchResult = get_mission_num_pos(self.ctx, self.mission_num, screen)
        if num_result is None:
            # 找不到目标关卡 往右滑动找找
            point_start = CHOOSE_MISSION_RECT.center
            point_end = CHOOSE_MISSION_RECT.center + Point(-200, 0)
            self.ctx.controller.drag_to(point_end, point_start)
            time.sleep(0.5)
            return Operation.round_retry('未找到关卡')

        if self.ctx.controller.click(num_result.center):
            return Operation.round_success()
        else:
            return Operation.round_retry('点击关卡失败')

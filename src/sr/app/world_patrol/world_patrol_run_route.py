from typing import ClassVar

import sr.const.operation_const
from basic import Point
from basic.i18_utils import gt
from basic.log_utils import log
from sr.app.world_patrol import WorldPatrolRouteId, WorldPatrolRoute
from sr.const import operation_const, map_const
from sr.const.map_const import Region
from sr.context import Context
from sr.image.sceenshot import screen_state
from sr.operation import Operation, OperationResult, OperationFail, StateOperation, \
    StateOperationNode, OperationOneRoundResult, StateOperationEdge
from sr.operation.combine.transport import Transport
from sr.operation.unit.enter_auto_fight import EnterAutoFight
from sr.operation.unit.interact import Interact
from sr.operation.unit.move import MoveDirectly
from sr.operation.unit.team import CheckTeamMembersInWorld
from sr.operation.unit.wait import WaitInWorld, WaitInSeconds
from sr.screen_area.dialog import ScreenDialog
from sr.screen_area.normal_world import ScreenNormalWorld


class WorldPatrolRunRoute(StateOperation):

    STATUS_ALL_DONE: ClassVar[str] = '执行结束'

    def __init__(self, ctx: Context,
                 route_id: WorldPatrolRouteId,
                 technique_fight: bool = False):
        """
        运行一条锄地路线
        :param ctx:
        :param route_id: 路线ID
        """
        self.route: WorldPatrolRoute = WorldPatrolRoute(route_id)
        self.op_idx: int = -2
        self.current_pos: Point = self.route.tp.tp_pos
        self.current_region: Region = self.route.tp.region
        self.technique_fight: bool = technique_fight  # 使用秘技开怪

        edges = []
        tp = StateOperationNode('传送', op=Transport(ctx, self.route.tp))
        check_members = StateOperationNode('检测组队', self._check_members)
        edges.append(StateOperationEdge(tp, check_members))

        use_tech = StateOperationNode('使用秘技', self._use_tech)
        edges.append(StateOperationEdge(check_members, use_tech))

        op_node = StateOperationNode('执行路线指令', self._next_op)
        edges.append(StateOperationEdge(use_tech, op_node))
        edges.append(StateOperationEdge(op_node, op_node, ignore_status=True))

        finish = StateOperationNode('结束', self._finish)
        edges.append(StateOperationEdge(op_node, finish, status=WorldPatrolRunRoute.STATUS_ALL_DONE))

        super().__init__(ctx,
                         op_name='%s %s' % (gt('锄地路线', 'ui'), self.route.display_name),
                         edges=edges,
                         )

    def _init_before_execute(self):
        super()._init_before_execute()
        self.op_idx: int = -1
        self.current_pos: Point = self.route.tp.tp_pos
        self.current_region: Region = self.route.tp.region
        log.info('准备执行线路 %s', self.route.display_name)
        log.info('感谢以下人员提供本路线 %s', self.route.author_list)

    def _check_members(self) -> OperationOneRoundResult:
        """
        检测队员
        :return:
        """
        check_members = CheckTeamMembersInWorld(self.ctx)
        check_members_result = check_members.execute()

        return Operation.round_by_op(check_members_result)

    def _use_tech(self) -> OperationOneRoundResult:
        """
        如果是秘技开怪 且是上buff类的 就在路线运行前上buff
        :return:
        """
        if not self.technique_fight or not self.ctx.is_buff_technique:
            return Operation.round_success()

        screen = self.screenshot()

        state = screen_state.get_world_patrol_screen_state(screen, self.ctx.im, self.ctx.ocr,
                                                           in_world=True, fast_recover=True)
        if state == ScreenDialog.FAST_RECOVER_TITLE.value.text:  # 使用秘技后出现快速恢复对话框
            self.ctx.technique_used = False
            click = self.find_and_click_area(ScreenDialog.FAST_RECOVER_CONFIRM.value, screen)
            if click == Operation.OCR_CLICK_SUCCESS:
                return Operation.round_wait(wait=0.5)
            else:
                return Operation.round_retry('点击确认失败', wait=1.5)
        elif not self.ctx.technique_used:
            if state == ScreenNormalWorld.CHARACTER_ICON.value.status:
                self.ctx.controller.use_technique()
                self.ctx.technique_used = True
                return Operation.round_wait(wait=1.5)
            else:
                return Operation.round_retry('未在大世界画面', wait=1)
        else:
            return Operation.round_success()

    def _next_op(self) -> OperationOneRoundResult:
        """
        下一个操作指令
        :return:
        """
        self.op_idx += 1

        # if self.op_idx == 0:  # 测试传送点用
        #     return OperationSuccess(self.ctx, status=WorldPatrolRunRoute.STATUS_ALL_DONE)

        if self.op_idx >= len(self.route.route_list):
            return Operation.round_success(WorldPatrolRunRoute.STATUS_ALL_DONE)

        route_item = self.route.route_list[self.op_idx]
        next_route_item = self.route.route_list[self.op_idx + 1] if self.op_idx + 1 < len(self.route.route_list) else None

        if route_item['op'] in [operation_const.OP_MOVE, operation_const.OP_SLOW_MOVE]:
            op = self.move(route_item, next_route_item)
        elif route_item['op'] == operation_const.OP_PATROL:
            op = EnterAutoFight(self.ctx, use_technique=self.technique_fight)
        elif route_item['op'] == operation_const.OP_INTERACT:
            op = Interact(self.ctx, route_item['data'])
        elif route_item['op'] == operation_const.OP_WAIT:
            op = self.wait(route_item['data'][0], float(route_item['data'][1]))
        elif route_item['op'] == operation_const.OP_UPDATE_POS:
            next_pos = Point(route_item['data'][0], route_item['data'][1])
            self._update_pos_after_op(OperationResult(True, data=next_pos))
            return Operation.round_success()
        else:
            return Operation.round_fail(status='错误的锄大地指令 %s' % route_item['op'])

        return Operation.round_by_op(op.execute())

    def move(self, route_item, next_route_item) -> Operation:
        """
        移动到某个点
        :param route_item: 本次指令
        :param next_route_item: 下次指令
        :return:
        """
        current_pos = self.current_pos
        current_lm_info = self.ctx.ih.get_large_map(self.current_region)

        next_pos = Point(route_item['data'][0], route_item['data'][1])
        next_lm_info = None
        if len(route_item['data']) > 2:  # 需要切换层数
            next_region = map_const.region_with_another_floor(current_lm_info.region, route_item['data'][2])
            next_lm_info = self.ctx.ih.get_large_map(next_region)

        stop_afterwards = not (
                next_route_item is not None and
                next_route_item['op'] in [operation_const.OP_MOVE, operation_const.OP_SLOW_MOVE]
        )
        no_run = route_item['op'] == operation_const.OP_SLOW_MOVE

        return MoveDirectly(self.ctx, current_lm_info, next_lm_info=next_lm_info,
                            target=next_pos, start=current_pos,
                            stop_afterwards=stop_afterwards, no_run=no_run,
                            technique_fight=self.technique_fight,
                            op_callback=self._update_pos_after_op)

    def _update_pos_after_op(self, op_result: OperationResult):
        """
        移动后更新坐标
        :param op_result:
        :return:
        """
        if not op_result.success:
            return

        self.current_pos = op_result.data

        route_item = self.route.route_list[self.op_idx]
        if len(route_item['data']) > 2:
            self.current_region = map_const.region_with_another_floor(self.current_region, route_item['data'][2])

    def wait(self, wait_type: str, seconds: float) -> Operation:
        """
        等待
        :param wait_type: 等待类型
        :param seconds: 等待秒数
        :return:
        """
        if wait_type == 'in_world':
            return WaitInWorld(self.ctx, seconds, wait_after_success=1)  # 多等待一秒 动画后界面完整显示需要点时间
        elif wait_type == sr.const.operation_const.WAIT_TYPE_SECONDS:
            return WaitInSeconds(self.ctx, seconds)
        else:
            return OperationFail(self.ctx, status='错误的wait类型 %s' % wait_type)

    def _finish(self) -> OperationOneRoundResult:
        """
        路线执行完毕
        :return:
        """
        return Operation.round_success()

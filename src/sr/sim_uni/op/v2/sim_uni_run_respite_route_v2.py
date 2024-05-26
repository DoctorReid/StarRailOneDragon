from typing import List, Optional

from basic import Point
from basic.img import cv2_utils
from sr.context import Context
from sr.image.sceenshot import mini_map, MiniMapInfo
from sr.operation import StateOperationEdge, StateOperationNode, OperationOneRoundResult, Operation
from sr.operation.unit.interact import Interact
from sr.operation.unit.move import MoveWithoutPos
from sr.screen_area.screen_normal_world import ScreenNormalWorld
from sr.sim_uni.op.sim_uni_battle import SimUniEnterFight
from sr.sim_uni.op.sim_uni_event import SimUniEvent
from sr.sim_uni.op.v2.sim_uni_move_v2 import SimUniMoveToInteractByDetect
from sr.sim_uni.op.v2.sim_uni_run_route_base_v2 import SimUniRunRouteBase
from sr.sim_uni.sim_uni_const import SimUniLevelTypeEnum, SimUniLevelType
from sryolo.detector import draw_detections


class SimUniRunRespiteRouteV2(SimUniRunRouteBase):

    def __init__(self, ctx: Context, level_type: SimUniLevelType = SimUniLevelTypeEnum.ELITE.value):
        edges: List[StateOperationEdge] = []

        before_route = StateOperationNode('区域开始前', self._before_route)

        destroy = StateOperationNode('攻击罐子', self._destroy_objects)
        edges.append(StateOperationEdge(before_route, destroy))

        # 小地图有事件的话就走小地图
        check_mm = StateOperationNode('识别小地图黑塔', self._check_mm_icon)
        edges.append(StateOperationEdge(destroy, check_mm))
        move_by_mm = StateOperationNode('按小地图朝黑塔移动', self._move_by_mm)
        edges.append(StateOperationEdge(check_mm, move_by_mm, status=SimUniRunRouteBase.STATUS_WITH_MM_EVENT))

        # 小地图没有事件的话就靠识别
        detect_screen = StateOperationNode('识别画面黑塔', self._detect_screen)
        edges.append(StateOperationEdge(check_mm, detect_screen, status=SimUniRunRouteBase.STATUS_NO_MM_EVENT))
        # 识别到就移动
        move_by_detect = StateOperationNode('按画面朝黑塔移动', self._move_by_detect)
        edges.append(StateOperationEdge(detect_screen, move_by_detect, status=SimUniRunRouteBase.STATUS_WITH_DETECT_EVENT))

        # 走到了就进行交互
        interact = StateOperationNode('交互', self._interact)
        edges.append(StateOperationEdge(move_by_mm, interact))
        edges.append(StateOperationEdge(move_by_detect, interact, status=SimUniMoveToInteractByDetect.STATUS_ARRIVAL))

        # 交互了之后开始事件判断
        event = StateOperationNode('黑塔', self._handle_event)
        edges.append(StateOperationEdge(interact, event))

        # 事件之后 识别下层入口
        check_entry = StateOperationNode('识别下层入口', self._check_next_entry)
        edges.append(StateOperationEdge(event, check_entry))
        # 识别不到事件、交互失败 也识别下层入口
        edges.append(StateOperationEdge(detect_screen, check_entry, status=SimUniRunRouteBase.STATUS_NO_DETECT_EVENT))
        edges.append(StateOperationEdge(interact, check_entry, success=False))
        # 之前已经处理过事件了 识别下层人口
        edges.append(StateOperationEdge(check_mm, check_entry, status=SimUniRunRouteBase.STATUS_HAD_EVENT))
        edges.append(StateOperationEdge(detect_screen, check_entry, status=SimUniRunRouteBase.STATUS_HAD_EVENT))
        # 找到了下层入口就开始移动
        move_to_next = StateOperationNode('向下层移动', self._move_to_next)
        edges.append(StateOperationEdge(check_entry, move_to_next, status=SimUniRunRouteBase.STATUS_WITH_ENTRY))
        # 找不到下层入口就转向找目标 重新开始
        turn = StateOperationNode('转动找目标', self._turn_when_nothing)
        edges.append(StateOperationEdge(check_entry, turn, status=SimUniRunRouteBase.STATUS_NO_ENTRY))
        edges.append(StateOperationEdge(turn, check_mm))

        super().__init__(ctx, level_type=level_type,
                         edges=edges,
                         specified_start_node=before_route
                         )

        self.mm_icon_pos: Optional[Point] = None  # 小地图上黑塔的坐标
        self.event_handled: bool = False  # 已经处理过事件了

    def _destroy_objects(self) -> OperationOneRoundResult:
        """
        攻击罐子
        :return:
        """
        # 兼容近战角色 稍微往前走一点再进行攻击
        self.ctx.controller.move('w', 0.5)
        # 注意要使用这个op 防止弹出祝福之类卡死
        op = SimUniEnterFight(self.ctx, disposable=True, first_state=ScreenNormalWorld.CHARACTER_ICON.value.status)
        return self.round_by_op(op.execute())

    def _check_mm_icon(self) -> OperationOneRoundResult:
        """
        识别小地图上的黑塔图标
        :return:
        """
        if self.event_handled:  # 已经交互过事件了
            return self.round_success(status=SimUniRunRouteBase.STATUS_HAD_EVENT)
        screen = self.screenshot()
        mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
        mm_info: MiniMapInfo = mini_map.analyse_mini_map(mm)
        mrl = self.ctx.im.match_template(mm_info.origin_del_radio, template_id='mm_sp_herta', template_sub_dir='sim_uni')
        if mrl.max is not None:
            self.mm_icon_pos = mrl.max.center
            return self.round_success(status=SimUniRunRouteBase.STATUS_WITH_MM_EVENT)
        else:
            return self.round_success(status=SimUniRunRouteBase.STATUS_NO_MM_EVENT)

    def _move_by_mm(self) -> OperationOneRoundResult:
        """
        按小地图的图标位置机械移动
        :return:
        """
        self.nothing_times = 0
        self.moved_to_target = True
        # 按照目前的固定布局 走向黑塔后 下层入口必定往左转更快发现
        self.turn_direction_when_nothing = -1
        op = MoveWithoutPos(self.ctx, start=self.ctx.game_config.mini_map_pos.mm_center, target=self.mm_icon_pos)
        return self.round_by_op(op.execute())

    def _detect_screen(self) -> OperationOneRoundResult:
        """
        识别游戏画面上是否有事件牌
        :return:
        """
        if self.event_handled:  # 已经交互过事件了
            return self.round_success(status=SimUniRunRouteBase.STATUS_HAD_EVENT)
        self._view_down()
        screen = self.screenshot()

        frame_result = self.ctx.sim_uni_yolo.detect(screen)

        with_event: bool = False
        for result in frame_result.results:
            if result.detect_class.class_cate == '模拟宇宙黑塔':
                with_event = True
                break

        if with_event:
            return self.round_success(status=SimUniRunRouteBase.STATUS_WITH_DETECT_EVENT)
        else:
            if self.ctx.one_dragon_config.is_debug:
                if self.nothing_times == 1:
                    self.save_screenshot()
                cv2_utils.show_image(draw_detections(frame_result), win_name='respite_detect_screen')
            return self.round_success(SimUniRunRouteBase.STATUS_NO_DETECT_EVENT)

    def _move_by_detect(self) -> OperationOneRoundResult:
        """
        根据画面识别结果走向事件
        :return:
        """
        self.nothing_times = 0
        self.moved_to_target = True
        # 按照目前的固定布局 走向黑塔后 下层入口必定往左转更快发现
        self.turn_direction_when_nothing = -1
        op = SimUniMoveToInteractByDetect(self.ctx,
                                          interact_class='模拟宇宙黑塔',
                                          interact_word='黑塔',
                                          interact_during_move=False)
        return self.round_by_op(op.execute())

    def _interact(self) -> OperationOneRoundResult:
        """
        尝试交互
        :return:
        """
        op = Interact(self.ctx, '黑塔', lcs_percent=0.1, single_line=True)
        return self.round_by_op(op.execute())

    def _handle_event(self) -> OperationOneRoundResult:
        """
        事件处理
        :return:
        """
        self.event_handled = True
        op = SimUniEvent(self.ctx, skip_first_screen_check=False)
        return self.round_by_op(op.execute())

from typing import Optional

from basic import Point
from basic.img import cv2_utils
from sr.context.context import Context
from sr.image.sceenshot import mini_map, MiniMapInfo
from sr.operation import StateOperationNode, OperationOneRoundResult
from sr.operation.unit.interact import Interact
from sr.operation.unit.move import MoveWithoutPos
from sr.screen_area.screen_normal_world import ScreenNormalWorld
from sr.sim_uni.op.sim_uni_battle import SimUniEnterFight
from sr.sim_uni.op.sim_uni_event import SimUniEvent
from sr.sim_uni.op.sim_uni_move.sim_uni_move_to_interact_by_detect import SimUniMoveToInteractByDetect
from sr.sim_uni.op.v2.sim_uni_run_route_base_v2 import SimUniRunRouteBaseV2
from sr.sim_uni.sim_uni_const import SimUniLevelTypeEnum, SimUniLevelType
from sryolo.detector import draw_detections


class SimUniRunRespiteRouteV2(SimUniRunRouteBaseV2):

    def __init__(self, ctx: Context, level_type: SimUniLevelType = SimUniLevelTypeEnum.RESPITE.value):
        SimUniRunRouteBaseV2.__init__(self, ctx, level_type=level_type)

    def add_edges_and_nodes(self) -> None:
        """
        初始化前 添加边和节点 由子类实行
        :return:
        """
        before_route = StateOperationNode('区域开始前', self._before_route)

        destroy = StateOperationNode('攻击罐子', self._destroy_objects)
        self.add_edge(before_route, destroy)

        # 小地图有事件的话就走小地图
        check_mm = StateOperationNode('识别小地图黑塔', self._check_mm_icon)
        self.add_edge(destroy, check_mm)
        move_by_mm = StateOperationNode('按小地图朝黑塔移动', self._move_by_mm)
        self.add_edge(check_mm, move_by_mm, status=SimUniRunRouteBaseV2.STATUS_WITH_MM_EVENT)

        # 小地图没有事件的话就靠识别
        detect_screen = StateOperationNode('识别画面黑塔', self._detect_screen)
        self.add_edge(check_mm, detect_screen, status=SimUniRunRouteBaseV2.STATUS_NO_MM_EVENT)
        # 已经处理过事件的 也进入这里用YOLO识别入口
        self.add_edge(check_mm, detect_screen, status=SimUniRunRouteBaseV2.STATUS_HAD_EVENT)
        # 识别到就移动
        move_by_detect = StateOperationNode('按画面朝黑塔移动', self._move_by_detect)
        self.add_edge(detect_screen, move_by_detect, status=SimUniRunRouteBaseV2.STATUS_WITH_DETECT_EVENT)

        # 走到了就进行交互
        interact = StateOperationNode('交互', self._interact)
        self.add_edge(move_by_mm, interact)
        self.add_edge(move_by_detect, interact, status=SimUniMoveToInteractByDetect.STATUS_ARRIVAL)

        # 交互了之后开始事件判断
        event = StateOperationNode('黑塔', self._handle_event)
        self.add_edge(interact, event)

        # 事件之后 识别下层入口
        check_entry = StateOperationNode('识别下层入口', self._check_next_entry)
        self.add_edge(event, check_entry)
        # 识别不到事件、交互失败 也识别下层入口
        self.add_edge(detect_screen, check_entry, status=SimUniRunRouteBaseV2.STATUS_NO_DETECT_EVENT)
        self.add_edge(interact, check_entry, success=False)
        # 之前已经处理过事件了 识别下层人口
        self.add_edge(check_mm, check_entry, status=SimUniRunRouteBaseV2.STATUS_HAD_EVENT)
        self.add_edge(detect_screen, check_entry, status=SimUniRunRouteBaseV2.STATUS_HAD_EVENT)
        # 找到了下层入口就开始移动
        move_to_next = StateOperationNode('向下层移动', self._move_to_next)
        self.add_edge(check_entry, move_to_next, status=SimUniRunRouteBaseV2.STATUS_WITH_ENTRY)
        self.add_edge(detect_screen, move_to_next, status=SimUniRunRouteBaseV2.STATUS_WITH_ENTRY)
        # 找不到下层入口就转向找目标 重新开始
        turn = StateOperationNode('转动找目标', self._turn_when_nothing)
        self.add_edge(check_entry, turn, status=SimUniRunRouteBaseV2.STATUS_NO_ENTRY)
        # 移动到下层入口失败时 也转动找目标
        # 可能1 走过了 没交互成功
        # 可能2 识别错了未激活的入口 移动过程中被攻击了
        self.add_edge(move_to_next, turn, success=False)
        # 转动完重新开始目标识别
        self.add_edge(turn, check_mm)

    def handle_init(self) -> Optional[OperationOneRoundResult]:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        可以返回初始化后判断的结果
        - 成功时跳过本指令
        - 失败时立刻返回失败
        - 不返回时正常运行本指令
        """
        SimUniRunRouteBaseV2.handle_init(self)
        self.move_by_mm_time: int = 0  # 按小地图移动的次数
        self.mm_icon_pos: Optional[Point] = None  # 小地图上黑塔的坐标
        self.event_handled: bool = False  # 已经处理过事件了

        return None

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
        if self.ctx.sim_uni_challenge_config.skip_herta:  # 跳过黑塔
            self.event_handled = True
        if self.move_by_mm_time >= 2:
            # 如果移动了2次都没有交互完 说明小地图没有这个图标 只是识别错了
            self.event_handled = True
        if self.event_handled:  # 已经交互过事件了
            return self.round_success(status=SimUniRunRouteBaseV2.STATUS_HAD_EVENT)
        screen = self.screenshot()
        mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
        mm_info: MiniMapInfo = mini_map.analyse_mini_map(mm)
        mrl = self.ctx.im.match_template(mm_info.origin_del_radio, template_id='mm_sp_herta', template_sub_dir='sim_uni',
                                         threshold=0.7)
        if mrl.max is not None:
            self.mm_icon_pos = mrl.max.center
            return self.round_success(status=SimUniRunRouteBaseV2.STATUS_WITH_MM_EVENT)
        else:
            if not self.event_handled and not self.is_level_type_correct(screen):
                # 如何没有交互过 又没有小地图图标 可能是之前楼层类型判断错了
                return self.round_fail(status=SimUniRunRouteBaseV2.STATUS_WRONG_LEVEL_TYPE)
            return self.round_success(status=SimUniRunRouteBaseV2.STATUS_NO_MM_EVENT)

    def _move_by_mm(self) -> OperationOneRoundResult:
        """
        按小地图的图标位置机械移动
        :return:
        """
        self.move_by_mm_time += 1
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
        self.detect_entry = False
        self._view_down()
        screen = self.screenshot()

        frame_result = self.ctx.yolo_detector.sim_uni_yolo.detect(screen)

        with_event: bool = False
        for result in frame_result.results:
            if result.detect_class.class_cate == '模拟宇宙黑塔':
                with_event = True
            elif result.detect_class.class_cate == '模拟宇宙下层入口':
                self.detect_entry = True

        if with_event and not self.event_handled:
            return self.round_success(status=SimUniRunRouteBaseV2.STATUS_WITH_DETECT_EVENT)
        elif self.detect_entry:
            return self.round_success(status=SimUniRunRouteBaseV2.STATUS_WITH_ENTRY)
        elif self.event_handled:  # 已经交互过事件了
            return self.round_success(status=SimUniRunRouteBaseV2.STATUS_HAD_EVENT)
        else:
            if self.ctx.one_dragon_config.is_debug:
                if self.nothing_times == 1:
                    self.save_screenshot()
                cv2_utils.show_image(draw_detections(frame_result), win_name='respite_detect_screen')
            return self.round_success(SimUniRunRouteBaseV2.STATUS_NO_DETECT_EVENT)

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

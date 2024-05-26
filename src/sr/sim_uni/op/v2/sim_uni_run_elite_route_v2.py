from typing import Optional, Callable, List

from basic.img import cv2_utils
from basic.log_utils import log
from sr.context import Context
from sr.image.sceenshot import mini_map
from sr.operation import StateOperationEdge, StateOperationNode, Operation, OperationOneRoundResult
from sr.sim_uni.op.sim_uni_battle import SimUniFightElite
from sr.sim_uni.op.sim_uni_exit import SimUniExit
from sr.sim_uni.op.sim_uni_reward import SimUniReward
from sr.sim_uni.op.v2.sim_uni_move_v2 import SimUniMoveToEnemyByMiniMap, SimUniMoveToInteractByDetect
from sr.sim_uni.op.v2.sim_uni_run_route_base_v2 import SimUniRunRouteBaseV2
from sr.sim_uni.sim_uni_const import SimUniLevelType, SimUniLevelTypeEnum
from sryolo.detector import draw_detections


class SimUniRunEliteRouteV2(SimUniRunRouteBaseV2):

    def __init__(self, ctx: Context, level_type: SimUniLevelType = SimUniLevelTypeEnum.ELITE.value,
                 max_reward_to_get: int = 0,
                 get_reward_callback: Optional[Callable[[int, int], None]] = None,):
        """
        区域-精英
        1. 检查小地图是否有红点 有就向红点移动
        2. 开怪
        3. 领取奖励
        4. 朝下层移动
        :param ctx: 上下文
        :param level_type: 楼层类型
        :param max_reward_to_get: 最多获取多少次奖励
        :param get_reward_callback: 获取奖励后的回调
        """
        edges: List[StateOperationEdge] = []

        before_route = StateOperationNode('区域开始前', self._before_route)

        check_red = StateOperationNode('识别小地图红点', self._check_red)
        edges.append(StateOperationEdge(before_route, check_red))

        # 没红点时 往前走一段距离
        move_no_red = StateOperationNode('无红点处理', self._move_forward_if_no_red)
        edges.append(StateOperationEdge(check_red, move_no_red, status=SimUniRunRouteBaseV2.STATUS_NO_RED))

        # 有红点就靠红点移动
        move_by_red = StateOperationNode('向红点移动', self._move_by_red)
        edges.append(StateOperationEdge(check_red, move_by_red, status=SimUniRunRouteBaseV2.STATUS_WITH_RED))

        # 到达精英怪旁边发起攻击
        start_fight = StateOperationNode('进入战斗', self._enter_fight)
        edges.append(StateOperationEdge(move_by_red, start_fight, status=SimUniMoveToEnemyByMiniMap.STATUS_ARRIVAL))

        # 战斗后处理
        after_fight = StateOperationNode('战斗后处理', self._after_fight)
        edges.append(StateOperationEdge(start_fight, after_fight))

        # 战斗后识别沉浸奖励装置
        detect_reward = StateOperationNode('识别沉浸奖励', self._detect_reward)
        edges.append(StateOperationEdge(after_fight, detect_reward))
        edges.append(StateOperationEdge(check_red, detect_reward, status=SimUniRunRouteBaseV2.STATUS_HAD_FIGHT))
        # 没红点时 识别沉浸奖励装置
        edges.append(StateOperationEdge(move_no_red, detect_reward))

        # 朝沉浸奖励装置移动
        move_to_reward = StateOperationNode('朝沉浸奖励移动', self._move_to_reward)
        edges.append(StateOperationEdge(detect_reward, move_to_reward, status=SimUniRunRouteBaseV2.STATUS_WITH_DETECT_REWARD))

        # 移动超时 卡住了
        detect_timeout = StateOperationNode('移动超时', self._after_detect_timeout)
        edges.append(StateOperationEdge(move_to_reward, detect_timeout, success=False, status=Operation.STATUS_TIMEOUT))
        edges.append(StateOperationEdge(detect_timeout, move_to_reward))

        # 领取奖励
        get_reward = StateOperationNode('领取沉浸奖励', self._get_reward)
        edges.append(StateOperationEdge(move_to_reward, get_reward, status=SimUniMoveToInteractByDetect.STATUS_INTERACT))

        # 无需领奖励 或者 领取奖励后 识别下层入口
        check_entry = StateOperationNode('识别下层入口', self._check_next_entry)
        edges.append(StateOperationEdge(detect_reward, check_entry, status=SimUniRunRouteBaseV2.STATUS_NO_NEED_REWARD))
        edges.append(StateOperationEdge(get_reward, check_entry))
        # 找到了下层入口就开始移动
        move_to_next = StateOperationNode('向下层移动', self._move_to_next)
        edges.append(StateOperationEdge(check_entry, move_to_next, status=SimUniRunRouteBaseV2.STATUS_WITH_ENTRY))
        # 找不到下层入口 就转向重新开始
        turn = StateOperationNode('转动找目标', self._turn_when_nothing)
        edges.append(StateOperationEdge(check_entry, turn, status=SimUniRunRouteBaseV2.STATUS_NO_ENTRY))
        edges.append(StateOperationEdge(turn, check_red))
        # 需要领取沉浸奖励 而又找不到沉浸奖励时 也转向重新开始
        edges.append(StateOperationEdge(detect_reward, turn, status=SimUniRunRouteBaseV2.STATUS_NO_DETECT_REWARD))

        # 首领后退出
        boss_exit = StateOperationNode('首领后退出', self._boss_exit)
        edges.append(StateOperationEdge(check_entry, boss_exit, status=SimUniRunRouteBaseV2.STATUS_BOSS_EXIT))

        super().__init__(ctx, level_type=level_type,
                         edges=edges,
                         specified_start_node=before_route
                         )

        self.had_fight: bool = False  # 已经进行过战斗了
        self.had_reward: bool = False  # 已经拿过沉浸奖励了
        self.max_reward_to_get: int = max_reward_to_get  # 最多获取多少次奖励
        self.get_reward_callback: Optional[Callable[[int, int], None]] = get_reward_callback  # 获取奖励后的回调

    def _check_red(self) -> OperationOneRoundResult:
        """
        检查小地图是否有红点
        :return:
        """
        if self.had_fight:
            return self.round_success(status=SimUniRunRouteBaseV2.STATUS_HAD_FIGHT)
        screen = self.screenshot()
        mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
        mm_info = mini_map.analyse_mini_map(mm)
        pos_list = mini_map.get_enemy_pos(mm_info)
        if len(pos_list) == 0:
            return self.round_success(status=SimUniRunRouteBaseV2.STATUS_NO_RED)
        else:
            return self.round_success(status=SimUniRunRouteBaseV2.STATUS_WITH_RED)

    def _move_forward_if_no_red(self) -> OperationOneRoundResult:
        """
        没红点时 又是没有战斗的情况
        - 重试进来没有精英怪
        - 精英怪太远了
        先尝试往前走一段距离 再进行后续识别 否则YOLO识别到入口 但老方法识别不到
        :return:
        """
        if not self.had_fight:
            self.ctx.controller.move('w', 2)

        return self.round_success()

    def _move_by_red(self) -> OperationOneRoundResult:
        """
        往小地图红点移动
        :return:
        """
        self.nothing_times = 0
        self.moved_to_target = True
        op = SimUniMoveToEnemyByMiniMap(self.ctx, no_attack=True, stop_after_arrival=True)
        return self.round_by_op(op.execute())

    def _enter_fight(self) -> OperationOneRoundResult:
        """
        移动到精英怪旁边之后 发起攻击
        :return:
        """
        op = SimUniFightElite(self.ctx)
        return self.round_by_op(op.execute())

    def _after_fight(self) -> OperationOneRoundResult:
        """
        精英怪战斗后
        :return:
        """
        self.had_fight = True
        self._turn_to_previous_angle()
        self.moved_to_target = True  # 与精英战斗后 该识别的目标都在附近了 就算识别不到也不需要往前走了

        return self.round_success()

    def _detect_reward(self) -> OperationOneRoundResult:
        if self.had_reward:
            log.debug('领取过沉浸奖励')
            return self.round_success(status=SimUniRunRouteBaseV2.STATUS_NO_NEED_REWARD)

        # 调试时候强制走到沉浸奖励
        if not self.ctx.one_dragon_config.is_debug and self.max_reward_to_get == 0:
            log.debug('不需要领取沉浸奖励')
            return self.round_success(status=SimUniRunRouteBaseV2.STATUS_NO_NEED_REWARD)

        # self._view_down()  # 入口和下层奖励 都比较大 应该不需要视角往下
        screen = self.screenshot()

        frame_result = self.ctx.sim_uni_yolo.detect(screen)

        detected: bool = False
        for result in frame_result.results:
            if result.detect_class.class_cate == '模拟宇宙沉浸奖励':
                detected = True
                break

        if detected:
            return self.round_success(status=SimUniRunRouteBaseV2.STATUS_WITH_DETECT_REWARD)
        else:
            if self.ctx.one_dragon_config.is_debug:
                if self.nothing_times == 1:
                    self.save_screenshot()
                cv2_utils.show_image(draw_detections(frame_result), win_name='SimUniRunEliteRouteV2')

            if self.had_fight and self.nothing_times <= 11:  # 战斗后 一定要找到沉浸奖励
                return self.round_success(SimUniRunRouteBaseV2.STATUS_NO_DETECT_REWARD)
            else:  # 重进的情况(没有战斗) 或者 找不到沉浸奖励太多次了 就不找了
                log.debug('没有战斗 或者 找不到沉浸奖励太多次了')
                return self.round_success(SimUniRunRouteBaseV2.STATUS_NO_NEED_REWARD)

    def _move_to_reward(self) -> OperationOneRoundResult:
        """
        朝沉浸装置移动
        :return:
        """
        # 按照目前的固定布局 从精英怪走向沉浸奖励后 下层入口必定往左转更快发现
        self.turn_direction_when_nothing = -1

        self.nothing_times = 0
        self.moved_to_target = True
        op = SimUniMoveToInteractByDetect(self.ctx,
                                          interact_class='模拟宇宙沉浸奖励',
                                          interact_word='沉浸奖励',
                                          interact_during_move=True)
        op_result = op.execute()
        return self.round_by_op(op_result, wait=1 if op_result.success else 0)  # 稍微等待画面加载

    def _get_reward(self) -> OperationOneRoundResult:
        """
        领取沉浸奖励
        :return:
        """
        self.had_reward = True
        self.detect_move_timeout_times = 0
        op = SimUniReward(self.ctx, self.max_reward_to_get, self.get_reward_callback)
        return self.round_by_op(op.execute())

    def _boss_exit(self) -> OperationOneRoundResult:
        """
        战胜首领后退出
        :return:
        """
        op = SimUniExit(self.ctx)
        return self.round_by_op(op.execute())

import time
from typing import Tuple, Optional, Callable, List, ClassVar

import numpy as np
from cv2.typing import MatLike

from basic import Point, cal_utils, Rect
from basic.i18_utils import gt
from basic.img import MatchResult, cv2_utils
from basic.img.os import save_debug_image
from basic.log_utils import log
from sr import cal_pos
from sr.cal_pos import VerifyPosInfo
from sr.context import Context
from sr.control import GameController
from sr.image.image_holder import ImageHolder
from sr.image.sceenshot import LargeMapInfo, MiniMapInfo, large_map, mini_map, screen_state
from sr.operation import OperationResult, OperationOneRoundResult, Operation, StateOperation, StateOperationNode, \
    StateOperationEdge
from sr.operation.unit.interact import check_move_interact
from sr.operation.unit.move import MoveDirectly
from sr.sim_uni.op.sim_uni_battle import SimUniEnterFight
from sr.sim_uni.sim_uni_challenge_config import SimUniChallengeConfig
from sr.sim_uni.sim_uni_const import SimUniLevelTypeEnum, SimUniLevelType, level_type_from_id
from sr.sim_uni.sim_uni_route import SimUniRoute


class MoveDirectlyInSimUni(MoveDirectly):
    """
    从当前位置 朝目标点直线前行
    有简单的脱困功能

    模拟宇宙专用
    - 不需要考虑特殊点
    - 不需要考虑多层地图
    - 战斗后需要选择祝福
    """
    def __init__(self, ctx: Context, lm_info: LargeMapInfo,
                 start: Point, target: Point,
                 config: Optional[SimUniChallengeConfig] = None,
                 stop_afterwards: bool = True,
                 no_run: bool = False,
                 no_battle: bool = False,
                 op_callback: Optional[Callable[[OperationResult], None]] = None,
                 ):
        MoveDirectly.__init__(
            self,
            ctx, lm_info,
            start, target, stop_afterwards=stop_afterwards,
            no_run=no_run, no_battle=no_battle,
            op_callback=op_callback)
        self.op_name = '%s %s' % (gt('模拟宇宙', 'ui'), gt('移动 %s -> %s') % (start, target))
        self.config: SimUniChallengeConfig = config

    def cal_pos(self, mm: MatLike, now_time: float) -> Tuple[Optional[Point], MiniMapInfo]:
        """
        根据上一次的坐标和行进距离 计算当前位置坐标
        :param mm: 小地图截图
        :param now_time: 当前时间
        :return:
        """
        # 根据上一次的坐标和行进距离 计算当前位置
        if self.last_rec_time > 0:
            if self.stop_move_time is not None:
                move_time = self.stop_move_time - self.last_rec_time  # 停止移动后的时间不应该纳入计算
            else:
                move_time = now_time - self.last_rec_time
            if move_time < 1:
                move_time = 1
        else:
            move_time = 1

        if self.ctx.pos_info.first_cal_pos_after_fight:
            move_time += 1  # 扩大范围 兼容攻击时产生的位移

        log.debug('上次记录时间 %.2f 停止移动时间 %.2f 当前时间 %.2f',
                  self.last_rec_time,
                  0 if self.stop_move_time is None else self.stop_move_time,
                  now_time)
        move_distance = self.ctx.controller.cal_move_distance_by_time(move_time)
        last_pos = self.pos[len(self.pos) - 1] if len(self.pos) > 0 else self.start_pos
        possible_pos = (last_pos.x, last_pos.y, move_distance)
        log.debug('准备计算人物坐标 使用上一个坐标为 %s 移动时间 %.2f 是否在移动 %s', possible_pos,
                  move_time, self.ctx.controller.is_moving)
        lm_rect = large_map.get_large_map_rect_by_pos(self.lm_info.gray.shape, mm.shape[:2], possible_pos)

        mm_info = mini_map.analyse_mini_map(mm)

        if len(self.pos) == 0:
            return self.start_pos, mm_info

        verify = VerifyPosInfo(last_pos=last_pos, max_distance=move_distance,
                               line_p1=self.start_pos, line_p2=self.target,
                               max_line_distance=40 if self.ctx.pos_info.first_cal_pos_after_fight else 20)
        try:
            next_pos = cal_pos.sim_uni_cal_pos(self.ctx.im, self.lm_info, mm_info,
                                               lm_rect=lm_rect,
                                               running=self.ctx.controller.is_moving,
                                               real_move_time=self.ctx.controller.get_move_time(),
                                               verify=verify)
        except Exception:
            next_pos = None
            log.error('识别坐标失败', exc_info=True)

        if next_pos is None:
            log.error('无法判断当前人物坐标')
            if self.ctx.one_dragon_config.is_debug:
                save_debug_image(mm, file_name='%s_%d_%d_%d_%s' %
                                               (self.lm_info.region.prl_id,
                                                possible_pos[0],
                                                possible_pos[1],
                                                int(possible_pos[2]),
                                                self.ctx.controller.is_moving)
                                 )

        return next_pos, mm_info

    def be_attacked(self, screen: MatLike) -> Optional[OperationOneRoundResult]:
        """
        判断当前是否在不在宇宙移动的画面
        即被怪物攻击了 等待至战斗完成
        :param screen: 屏幕截图
        :return:
        """
        if self.no_battle:
            return None
        if not screen_state.is_normal_in_world(screen, self.ctx.im):
            fight_start_time = time.time()
            self.last_auto_fight_fail = False
            self.ctx.controller.stop_moving_forward()
            if self.stop_move_time is None:
                self.stop_move_time = time.time()
            fight = SimUniEnterFight(self.ctx, config=self.config)
            fight_result = fight.execute()
            fight_end_time = time.time()
            if not fight_result.success:
                return Operation.round_fail(status=fight_result.status, data=fight_result.data)
            self.last_battle_time = fight_end_time
            self.last_rec_time += fight_end_time - fight_start_time  # 战斗可能很久 更改记录时间
            self.ctx.pos_info.first_cal_pos_after_fight = True
            # self.move_after_battle()
            return Operation.round_wait()
        return None

    def check_enemy_and_attack(self, mm: MatLike) -> Optional[OperationOneRoundResult]:
        """
        从小地图检测敌人 如果有的话 进入索敌
        :param mm: 小地图
        :return: 是否有敌人
        """
        if self.no_battle:
            return None
        if self.last_auto_fight_fail:  # 上一次索敌失败了 可能小地图背景有问题 等待下一次进入战斗画面刷新
            return None
        if not mini_map.is_under_attack(mm):
            return None

        # 停下来的任务交给了 SimUniEnterFight 这样可以取消停止移动造成的后摇
        # self.ctx.controller.stop_moving_forward()  # 先停下来再攻击
        if self.stop_move_time is None:
            self.stop_move_time = time.time()

        fight_start_time = time.time()
        fight = SimUniEnterFight(self.ctx, self.config)
        op_result = fight.execute()
        if not op_result.success:
            return Operation.round_fail(status=op_result.status, data=op_result.data)
        fight_end_time = time.time()

        self.last_auto_fight_fail = (op_result.status == SimUniEnterFight.STATUS_ENEMY_NOT_FOUND)
        self.last_battle_time = fight_end_time
        self.last_rec_time += fight_end_time - fight_start_time  # 战斗可能很久 更改记录时间
        self.ctx.pos_info.first_cal_pos_after_fight = True
        # self.move_after_battle()

        return Operation.round_wait()


class MoveWithoutPosInSimUni(StateOperation):

    STATUS_PAUSE: ClassVar[str] = '暂停结束'
    STATUS_ARRIVE: ClassVar[str] = '到达'

    def __init__(self, ctx: Context, enemy_pos: Point):
        """
        朝一个位置移动 先不使用疾跑
        :param ctx: 上下文
        :param enemy_pos: 以人物坐标为 (0, 0) 计算到的敌人的坐标
        """
        edges: List[StateOperationEdge] = []

        turn = StateOperationNode('转向', self._turn)
        move = StateOperationNode('移动', self._move)

        super().__init__(ctx,
                         op_name='%s %s %s' % (
                             gt('模拟宇宙', 'ui'),
                             gt('机械移动', 'ui'),
                             enemy_pos
                         ),
                         nodes=[turn, move]
                         )

        self.start_point = Point(0, 0)
        self.end_point = enemy_pos
        dis = cal_utils.distance_between(self.start_point, self.end_point)
        self.need_move_time: float = dis / self.ctx.controller.walk_speed
        self.ever_pause: bool = False  # 程序是否暂停过 暂停了就标记完成等待重新计算距离移动

    def _turn(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
        angle = mini_map.analyse_angle(mm)

        self.ctx.controller.turn_by_pos(self.start_point, self.end_point, angle)

        return Operation.round_success(wait=0.5)  # 等待转向结束

    def _move(self) -> OperationOneRoundResult:
        self.ctx.controller.start_moving_forward()
        return Operation.round_success()

    def _check_arrival(self) -> OperationOneRoundResult:
        if self.ever_pause:
            return Operation.round_success(MoveWithoutPosInSimUni.STATUS_PAUSE)
        if self.ctx.controller.get_move_time() >= self.need_move_time:
            return Operation.round_success(MoveWithoutPosInSimUni.STATUS_ARRIVE)

        return Operation.round_wait(wait=0.02)

    def on_pause(self, e=None):
        super().on_pause()
        self.ever_pause = True


class MoveToNextLevel(StateOperation):

    MOVE_TIME: ClassVar[float] = 1.5  # 每次移动的时间
    CHARACTER_CENTER: ClassVar[Point] = Point(960, 920)  # 界面上人物的中心点 取了脚底

    NEXT_CONFIRM_BTN: ClassVar[Rect] = Rect(1006, 647, 1330, 697)  # 确认按钮

    STATUS_ENTRY_NOT_FOUND: ClassVar[str] = '未找到下一层入口'
    STATUS_ENCOUNTER_FIGHT: ClassVar[str] = '遭遇战斗'

    def __init__(self, ctx: Context,
                 level_type: SimUniLevelType,
                 route: Optional[SimUniRoute] = None,
                 current_pos: Optional[Point] = None,
                 config: Optional[SimUniChallengeConfig] = None):
        """
        朝下一层入口走去 并且交互
        :param ctx:
        :param level_type: 当前楼层的类型 精英层的话 有可能需要确定
        :param route: 当前使用路线
        :param current_pos: 当前人物的位置
        :param config: 挑战配置
        """
        turn = StateOperationNode('转向入口', self._turn_to_next)
        move = StateOperationNode('移动交互', self._move_and_interact)
        confirm = StateOperationNode('确认', self._confirm)

        super().__init__(ctx, try_times=10,
                         op_name='%s %s' % (gt('模拟宇宙', 'ui'), gt('向下一层移动', 'ui')),
                         nodes=[turn, move, confirm]
                         )
        self.level_type: SimUniLevelType = level_type
        self.route: SimUniRoute = route
        self.current_pos: Optional[Point] = current_pos
        self.next_pos: Optional[Point] = None
        self.config: Optional[SimUniChallengeConfig] = config
        self.is_moving: bool = False  # 是否正在移动
        self.start_move_time: float = 0  # 开始移动的时间
        self.interacted: bool = False  # 是否已经交互了

    def _init_before_execute(self):
        super()._init_before_execute()
        self.is_moving = False
        self.interacted = False
        if self.route is None or self.route.next_pos_list is None or len(self.route.next_pos_list) == 0:
            self.next_pos = None
        else:
            avg_pos_x = np.mean([pos.x for pos in self.route.next_pos_list], dtype=np.uint16)
            avg_pos_y = np.mean([pos.y for pos in self.route.next_pos_list], dtype=np.uint16)
            self.next_pos = Point(avg_pos_x, avg_pos_y)

    def _turn_to_next(self) -> OperationOneRoundResult:
        """
        朝入口转向 方便看到所有的入口
        :return:
        """
        if self.route is None:  # 不是使用配置路线时 不需要先转向
            return Operation.round_success()
        if self.current_pos is None or self.next_pos is None:
            if self.ctx.one_dragon_config.is_debug:
                return Operation.round_fail('未配置下层入口')
            else:
                return Operation.round_success()
        screen = self.screenshot()

        if not screen_state.is_normal_in_world(screen, self.ctx.im):
            log.error('找下层入口时进入战斗 请反馈给作者 %s', self.route.display_name)
            if self.ctx.one_dragon_config.is_debug:
                return Operation.round_fail(MoveToNextLevel.STATUS_ENCOUNTER_FIGHT)
            op = SimUniEnterFight(self.ctx, self.config)
            op_result = op.execute()
            if op_result.success:
                return Operation.round_wait()
            else:
                return Operation.round_retry()

        mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
        mm_info: MiniMapInfo = mini_map.analyse_mini_map(mm)
        self.ctx.controller.turn_by_pos(self.current_pos, self.next_pos, mm_info.angle)

        return Operation.round_success(wait=0.5)  # 等待转动完成

    def _move_and_interact(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        in_world = screen_state.is_normal_in_world(screen, self.ctx.im)

        if not in_world:
            if self.interacted:
                # 兜底 - 如果已经不在大世界画面且又交互过了 就认为成功了
                return Operation.round_success()
            else:
                log.error('找下层入口时进入战斗 请反馈给作者 %s', '第九宇宙' if self.route is None else self.route.display_name)
                if self.ctx.one_dragon_config.is_debug:
                    return Operation.round_fail(MoveToNextLevel.STATUS_ENCOUNTER_FIGHT)
                op = SimUniEnterFight(self.ctx, self.config)
                op_result = op.execute()
                if op_result.success:
                    return Operation.round_wait()
                else:
                    return Operation.round_retry()

        interact = self._try_interact(screen)
        if interact is not None:
            return interact

        if self.is_moving:
            if time.time() - self.start_move_time > MoveToNextLevel.MOVE_TIME:
                self.ctx.controller.stop_moving_forward()
                self.is_moving = False
            return Operation.round_wait()
        else:
            type_list = MoveToNextLevel.get_next_level_type(screen, self.ctx.ih)
            if len(type_list) == 0:  # 当前没有入口 随便旋转看看
                # 因为前面已经转向了入口 所以就算被遮挡 只要稍微转一点应该就能看到了
                angle = (25 + 10 * self.op_round) * (1 if self.op_round % 2 == 0 else -1)  # 来回转动视角
                self.ctx.controller.turn_by_angle(angle)
                return Operation.round_retry(MoveToNextLevel.STATUS_ENTRY_NOT_FOUND, wait=1)

            target = self._get_target_entry(type_list)

            self._move_towards(target)
            return Operation.round_wait(wait=0.1)

    @staticmethod
    def get_next_level_type(screen: MatLike, ih: ImageHolder) -> List[MatchResult]:
        """
        获取当前画面中的下一层入口
        MatchResult.data 是对应的类型 SimUniLevelType
        :param screen: 屏幕截图
        :param ih: 图片加载器
        :return:
        """
        source_kps, source_desc = cv2_utils.feature_detect_and_compute(screen)

        result_list: List[MatchResult] = []

        for enum in SimUniLevelTypeEnum:
            level_type: SimUniLevelType = enum.value
            template = ih.get_sim_uni_template(level_type.template_id)

            result = cv2_utils.feature_match_for_one(source_kps, source_desc,
                                                     template.kps, template.desc,
                                                     template.origin.shape[1], template.origin.shape[0],
                                                     knn_distance_percent=0.6)

            if result is None:
                continue

            result.data = level_type
            result_list.append(result)

        return result_list

    def _get_target_entry(self, type_list: List[MatchResult]) -> MatchResult:
        """
        获取需要前往的入口
        :param type_list: 入口类型
        :return:
        """
        idx = MoveToNextLevel.match_best_level_type(type_list, self.config)
        return type_list[idx]

    @staticmethod
    def match_best_level_type(type_list: List[MatchResult], config: Optional[SimUniChallengeConfig]) -> int:
        """
        根据优先级 获取最优的入口类型
        :param type_list: 入口类型 保证长度大于0
        :param config: 挑战配置
        :return: 下标
        """
        if config is None:
            return 0

        for priority_id in config.level_type_priority:
            priority_level_type = level_type_from_id(priority_id)
            if priority_level_type is None:
                continue
            for idx, type_pos in enumerate(type_list):
                if type_pos.data == priority_level_type:
                    return idx

        return 0

    def _move_towards(self, target: MatchResult):
        """
        朝目标移动 先让人物转向 让目标就在人物前方
        :param target:
        :return:
        """
        angle_to_turn = self._get_angle_to_turn(target)
        self.ctx.controller.turn_by_angle(angle_to_turn)
        time.sleep(0.5)
        self.ctx.controller.start_moving_forward()
        self.start_move_time = time.time()
        self.is_moving = True

    def _get_angle_to_turn(self, target: MatchResult) -> float:
        """
        获取需要转向的角度
        角度的定义与 game_controller.turn_by_angle 一致
        正数往右转 人物角度增加；负数往左转 人物角度减少
        :param target:
        :return:
        """
        # 小地图用的角度 正右方为0 顺时针为正
        mm_angle = cal_utils.get_angle_by_pts(MoveToNextLevel.CHARACTER_CENTER, target.center)

        return mm_angle - 270

    def _try_interact(self, screen: MatLike) -> Optional[OperationOneRoundResult]:
        """
        尝试交互
        :param screen:
        :return:
        """
        if self._can_interact(screen):
            self.ctx.controller.interact(interact_type=GameController.MOVE_INTERACT_TYPE)
            log.debug('尝试交互进入下一层')
            self.interacted = True
            self.ctx.controller.stop_moving_forward()
            return Operation.round_wait(wait=0.1)
        else:
            return None

    def _can_interact(self, screen: MatLike) -> bool:
        """
        当前是否可以交互
        :param screen: 屏幕截图
        :return:
        """
        pos = check_move_interact(self.ctx, screen, '区域', single_line=True)
        return pos is not None

    def _confirm(self) -> OperationOneRoundResult:
        """
        精英层的确认
        :return:
        """
        if self.level_type != SimUniLevelTypeEnum.ELITE.value:
            return Operation.round_success()
        screen = self.screenshot()
        if not screen_state.is_normal_in_world(screen, self.ctx.im):
            click_confirm = self.ocr_and_click_one_line('确认', MoveToNextLevel.NEXT_CONFIRM_BTN,
                                                        screen=screen)
            if click_confirm == Operation.OCR_CLICK_SUCCESS:
                return Operation.round_success(wait=1)
            elif click_confirm == Operation.OCR_CLICK_NOT_FOUND:
                return Operation.round_success()
            else:
                return Operation.round_retry('点击确认失败', wait=0.25)
        else:
            return Operation.round_retry('在大世界页面')


class MoveToMiniMapInteractIcon(Operation):

    STATUS_ICON_NOT_FOUND: ClassVar[str] = '未找到图标'

    def __init__(self, ctx: Context, icon_template_id: str, interact_word: str):
        """
        朝小地图上的图标走去 并交互
        :param ctx:
        """
        super().__init__(ctx, try_times=5,
                         op_name='%s %s' % (
                             gt('模拟宇宙', 'ui'), 
                             gt('走向%s' % interact_word, 'ui'))
                         )

        self.icon_template_id: str = icon_template_id
        self.interact_word: str = interact_word

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        if not screen_state.is_normal_in_world(screen, self.ctx.im):
            log.info('未在大世界')
            return Operation.round_success()

        interact = self._try_interact(screen)
        if interact is not None:
            return interact

        mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
        target_pos = self._get_event_pos(mm)

        if target_pos is None:
            log.info('无图标')
            return Operation.round_retry(MoveToMiniMapInteractIcon.STATUS_ICON_NOT_FOUND, wait=0.5)
        else:
            start_pos = Point(mm.shape[1] // 2, mm.shape[0] // 2)
            angle = mini_map.analyse_angle(mm)
            self.ctx.controller.move_towards(start_pos, target_pos, angle)
            return Operation.round_wait()

    def _get_event_pos(self, mm: MatLike) -> Optional[Point]:
        """
        获取时间图标的位置
        :param mm:
        :return:
        """
        angle = mini_map.analyse_angle(mm)
        radio_to_del = mini_map.get_radio_to_del(angle)
        mm_del_radio = mini_map.remove_radio(mm, radio_to_del)
        source_kps, source_desc = cv2_utils.feature_detect_and_compute(mm_del_radio)
        template = self.ctx.ih.get_template(self.icon_template_id, sub_dir='sim_uni')
        mr = cv2_utils.feature_match_for_one(source_kps, source_desc,
                                             template.kps, template.desc,
                                             template.origin.shape[1], template.origin.shape[0])

        return None if mr is None else mr.center

    def _try_interact(self, screen: MatLike) -> Optional[OperationOneRoundResult]:
        """
        尝试交互
        :param screen:
        :return:
        """
        if self._can_interact(screen):
            self.ctx.controller.interact(interact_type=GameController.MOVE_INTERACT_TYPE)
            self.ctx.controller.stop_moving_forward()

            return Operation.round_wait(wait=0.25)
        else:
            return None

    def _can_interact(self, screen: MatLike) -> bool:
        """
        当前是否可以交互
        :param screen: 屏幕截图
        :return:
        """
        pos = check_move_interact(self.ctx, screen, self.interact_word, single_line=True)
        return pos is not None

    def _after_operation_done(self, result: OperationResult):
        super()._after_operation_done(result)
        self.ctx.controller.stop_moving_forward()

    def on_pause(self, e=None):
        super().on_pause(e)
        self.ctx.controller.stop_moving_forward()


class MoveToHertaInteract(MoveToMiniMapInteractIcon):
    
    def __init__(self, ctx: Context):
        super().__init__(ctx, 'mm_sp_herta', '黑塔')


class MoveToEventInteract(MoveToMiniMapInteractIcon):

    def __init__(self, ctx: Context):
        super().__init__(ctx, 'mm_sp_event', '事件')

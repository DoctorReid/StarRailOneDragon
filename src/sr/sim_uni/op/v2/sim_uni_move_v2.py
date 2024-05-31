import time
from typing import List, Optional, ClassVar

import numpy as np
from cv2.typing import MatLike

from basic import Point, cal_utils, str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr.const import game_config_const
from sr.context import Context
from sr.control import GameController
from sr.image.sceenshot import mini_map, MiniMapInfo, screen_state
from sr.operation import Operation, OperationOneRoundResult, OperationResult
from sr.operation.unit.interact import get_move_interact_words
from sr.operation.unit.move import GetRidOfStuck
from sr.screen_area.screen_normal_world import ScreenNormalWorld
from sr.sim_uni.op.move_in_sim_uni import MoveToNextLevel
from sr.sim_uni.op.sim_uni_battle import SimUniEnterFight
from sr.sim_uni.sim_uni_const import SimUniLevelType
from sryolo.detector import DetectObjectResult, draw_detections

_MAX_TURN_ANGLE = 15  # 由于目标识别没有纵深 判断的距离方向不准 限定转向角度慢慢转过去
_CHARACTER_POS = Point(960, 920)  # 人物脚底


def delta_angle_to_detected_object(obj: DetectObjectResult) -> float:
    """
    转向识别物体需要的偏移角度
    :param obj:
    :return: 偏移角度 正数往右转 负数往左转
    """
    obj_pos = Point((obj.x1 + obj.x2) / 2, obj.y2)  # 识别框底部

    # 小地图用的角度 正右方为0 顺时针为正
    mm_angle = cal_utils.get_angle_by_pts(_CHARACTER_POS, obj_pos)

    # 与画面正前方的偏移角度 就是需要转的角度
    turn_angle = mm_angle - 270

    return turn_angle


def turn_to_detected_object(ctx: Context, obj: DetectObjectResult) -> float:
    """
    转向一个识别到的物体
    :param ctx: 上下文
    :param obj: 检测物体
    :return: 转向角度 正数往右转 负数往左转
    """
    turn_angle = delta_angle_to_detected_object(obj)
    return turn_by_angle_slowly(ctx, turn_angle)


def turn_by_angle_slowly(ctx: Context, turn_angle: float) -> float:
    """
    缓慢转向 有一个最大的转向角度
    :param ctx: 上下文
    :param turn_angle: 转向角度
    :return: 真实转向角度
    """
    # 由于目前没有距离的推测 不要一次性转太多角度
    if turn_angle > _MAX_TURN_ANGLE:
        turn_angle = _MAX_TURN_ANGLE
    if turn_angle < -_MAX_TURN_ANGLE:
        turn_angle = -_MAX_TURN_ANGLE

    ctx.controller.turn_by_angle(turn_angle)
    return turn_angle


class SimUniMoveToEnemyByMiniMap(Operation):
    STATUS_ARRIVAL: ClassVar[str] = '已到达'
    STATUS_FIGHT: ClassVar[str] = '遭遇战斗'

    REC_POS_INTERVAL: ClassVar[float] = 0.1
    DIS_MAX_LEN: ClassVar[int] = 2 // REC_POS_INTERVAL  # 2秒没移动

    def __init__(self, ctx: Context, no_attack: bool = False, stop_after_arrival: bool = False):
        """
        从小地图上判断 向其中一个红点移动
        停下来的条件有
        - 距离红点过近
        - 被怪物锁定
        :param ctx: 上下文
        :param no_attack: 不主动发起攻击
        :param stop_after_arrival: 到达后停止 如果明确知道到达后会发起攻击 则可以不停止
        """
        super().__init__(ctx,
                         op_name=gt('向红点移动', 'ui'),
                         timeout_seconds=60
                         )

        self.current_pos: Point = Point(0, 0)
        """当前距离 默认是远点"""

        self.dis: List[float] = []
        """与红点的距离"""

        self.last_rec_time: float = 0
        """上一次记录距离的时间"""

        self.stuck_times: int = 0
        """被困次数"""

        self.no_attack: bool = no_attack
        """不发起主动攻击 适用于精英怪场合"""

        self.stop_after_arrival: bool = stop_after_arrival
        """到达后停止"""

    def _execute_one_round(self) -> OperationOneRoundResult:
        stuck = self.move_in_stuck()  # 先尝试脱困 再进行移动
        if stuck is not None:  # 只有脱困失败的时候会有返回结果
            return stuck

        now = time.time()
        screen = self.screenshot()

        if not screen_state.is_normal_in_world(screen, self.ctx.im):  # 不在大世界 可能被袭击了
            return self._enter_battle()

        if not self.no_attack:
            self.ctx.yolo_detector.detect_should_attack_in_world_async(screen, now)
            if self.ctx.yolo_detector.should_attack_in_world_last_result(now):
                return self._enter_battle()

        mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
        mm_info: MiniMapInfo = mini_map.analyse_mini_map(mm)
        enemy_pos_list = mini_map.get_enemy_pos(mm_info)

        if len(enemy_pos_list) == 0:  # 没有红点 可能太近被自身箭头覆盖了
            return self._arrive()

        # 最近的红点
        closest_dis: float = 999
        closest_pos: Point = None

        for pos in enemy_pos_list:
            dis = cal_utils.distance_between(self.current_pos, pos)
            if dis < closest_dis:
                closest_dis = dis
                closest_pos = pos

        if closest_dis < 10:
            return self._arrive()

        if len(self.dis) == 0:  # 第一个点 无条件放入
            return self._add_pos(now, closest_pos, closest_dis, mm_info.angle)

        # 只要开始移动了 目标点的角度应该在当前朝向附近
        del_angle = abs(cal_utils.get_angle_by_pts(self.current_pos, closest_pos) - 270)
        if del_angle > 20 and len(self.dis) > 3:
            pass  # 未知怎么处理

        return self._add_pos(now, closest_pos, closest_dis, mm_info.angle)

    def _add_pos(self, now: float, pos: Point, dis: float, angle: float) -> OperationOneRoundResult:
        """
        记录距离 每0.2秒一次 最多20个
        :param now: 这次运行的时间
        :param pos: 最近的红点位置
        :param dis: 最近的红点距离
        :param angle: 当前朝向
        :return:
        """
        if now - self.last_rec_time <= SimUniMoveToEnemyByMiniMap.REC_POS_INTERVAL:
            return self.round_wait()

        # 新距离比旧距离大 大概率已经到了一个点了 捕捉到的是第二个点
        if len(self.dis) > 0 and dis - self.dis[-1] > 10:
            return self._arrive()

        self.dis.append(dis)
        self.last_rec_time = now

        if len(self.dis) > SimUniMoveToEnemyByMiniMap.DIS_MAX_LEN:
            self.dis.pop(0)

        self.ctx.controller.move_towards(self.current_pos, pos, angle,
                                         run=self.ctx.game_config.run_mode != game_config_const.RUN_MODE_OFF)
        return self.round_wait()

    def move_in_stuck(self) -> Optional[OperationOneRoundResult]:
        """
        判断是否被困且进行移动
        :return: 如果被困次数过多就返回失败
        """
        if len(self.dis) == 0:
            return None

        first_dis = self.dis[0]
        last_dis = self.dis[len(self.dis) - 1]

        # 通过第一个坐标和最后一个坐标的距离 判断是否困住了
        if (len(self.dis) >= SimUniMoveToEnemyByMiniMap.DIS_MAX_LEN
                and last_dis >= first_dis):
            self.stuck_times += 1
            if self.stuck_times > 12:
                return self.round_fail('脱困失败')
            get_rid_of_stuck = GetRidOfStuck(self.ctx, self.stuck_times)
            stuck_op_result = get_rid_of_stuck.execute()
            if stuck_op_result.success:
                self.last_rec_time += stuck_op_result.data
        else:
            self.stuck_times = 0

        return None

    def _enter_battle(self) -> OperationOneRoundResult:
        """
        进入战斗
        :return:
        """
        op = SimUniEnterFight(self.ctx)
        op_result = op.execute()
        if op_result.success:
            return self.round_success(SimUniMoveToEnemyByMiniMap.STATUS_FIGHT)
        else:
            return self.round_by_op(op_result)

    def _arrive(self) -> OperationOneRoundResult:
        """
        到达红点后处理
        :return:
        """
        if self.stop_after_arrival:
            self.ctx.controller.stop_moving_forward()
        return self.round_success(SimUniMoveToEnemyByMiniMap.STATUS_ARRIVAL)


class SimUniMoveToEnemyByDetect(Operation):

    STATUS_ARRIVAL: ClassVar[str] = '已到达'
    STATUS_FIGHT: ClassVar[str] = '遭遇战斗'
    STATUS_NO_ENEMY: ClassVar[str] = '识别不到敌人'

    def __init__(self, ctx: Context):
        """
        根据画面识别怪的位置 朝怪移动。
        进入之前 应该确保当前朝向能识别到怪，本操作不会旋转去找怪
        停下来的条件有
        - 找不到怪
        - 被怪物锁定
        :param ctx:
        """
        super().__init__(ctx,
                         op_name=gt('向怪物移动', 'ui'),
                         timeout_seconds=20,  # 理论上移动目标都比较近 不可能20秒还没有到达
                         )

        self.no_enemy_times: int = 0  # 没有发现敌人的次数
        self.start_move_time: float = 0  # 开始移动的时间

        self.last_debug_time: float = 0

    def _execute_one_round(self) -> OperationOneRoundResult:
        now = time.time()
        screen = self.screenshot()

        # 不在大世界 可能被袭击了
        if not screen_state.is_normal_in_world(screen, self.ctx.im):
            return self.enter_battle()

        # 被怪锁定了
        mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
        mm_info = mini_map.analyse_mini_map(mm)
        if mini_map.is_under_attack_new(mm_info, danger=True):
            return self.enter_battle()

        # 移动2秒后 如果丢失了目标 停下来
        if self.ctx.controller.is_moving and now - self.start_move_time >= 2 and self.no_enemy_times > 0:
            self.ctx.controller.stop_moving_forward()
            return self.round_wait()

        # if now - self.last_debug_time > 0.5 and self.ctx.one_dragon_config.is_debug:
        #     self.save_screenshot()
        #     self.last_debug_time = now

        # 进行目标识别判断后续动作
        return self.detect_screen(screen)

    def enter_battle(self) -> OperationOneRoundResult:
        """
        进入战斗
        :return:
        """
        op = SimUniEnterFight(self.ctx)
        op_result = op.execute()
        if op_result.success:
            return self.round_success(SimUniMoveToEnemyByDetect.STATUS_FIGHT)
        else:
            return self.round_by_op(op_result)

    def detect_screen(self, screen: MatLike) -> OperationOneRoundResult:
        """
        对画面进行识别 根据结果进行后续判断
        :param screen:
        :return:
        """
        frame_result = self.ctx.yolo_detector.sim_uni_yolo.detect(screen)
        normal_enemy_result = []
        can_attack: bool = False
        for result in frame_result.results:
            if result.detect_class.class_cate == '普通怪':
                normal_enemy_result.append(result)
            elif result.detect_class.class_cate in ['界面提示被锁定', '界面提示可攻击']:
                can_attack = True

        if self.ctx.one_dragon_config.is_debug:
            cv2_utils.show_image(draw_detections(frame_result), win_name='SimUniMoveToEnemyByDetect')

        if can_attack:
            return self.enter_battle()
        elif len(normal_enemy_result) > 0:
            return self.handle_enemy(normal_enemy_result)
        else:
            return self.handle_no_enemy()

    def handle_no_enemy(self) -> OperationOneRoundResult:
        """
        处理当前画面没有中没有怪的情况
        :return:
        """
        self.no_enemy_times += 1
        if self.no_enemy_times >= 9:
            return self.round_fail(SimUniMoveToEnemyByDetect.STATUS_NO_ENEMY)

        # 第一次向右转一点 后续就在固定范围内晃动
        if self.no_enemy_times == 1:
            angle = 15
        else:
            angle = -30 if self.no_enemy_times % 2 == 0 else 30

        self.ctx.controller.turn_by_angle(angle)
        return self.round_wait(SimUniMoveToEnemyByDetect.STATUS_NO_ENEMY, wait=0.5)

    def handle_enemy(self, enemy_pos_list: List[DetectObjectResult]) -> OperationOneRoundResult:
        """
        处理有敌人的情况
        :param enemy_pos_list: 识别的敌人列表
        :return:
        """
        self.no_enemy_times = 0
        enemy = enemy_pos_list[0]  # 先固定找第一个
        turn_to_detected_object(self.ctx, enemy)
        self.ctx.controller.start_moving_forward()
        self.start_move_time = time.time()
        return self.round_wait()

    def _after_operation_done(self, result: OperationResult):
        """
        无论以哪种方式结束 都停止移动
        :param result:
        :return:
        """
        super()._after_operation_done(result)
        self.ctx.controller.stop_moving_forward()


class SimUniMoveToInteractByDetect(Operation):

    STATUS_ARRIVAL: ClassVar[str] = '已到达'
    STATUS_INTERACT: ClassVar[str] = '已交互'
    STATUS_NO_DETECT: ClassVar[str] = '识别不到交互目标'

    def __init__(self, ctx: Context,
                 interact_class: str,
                 interact_word: str,
                 interact_during_move: bool = False):
        """
        根据画面识别可交互内容的位置 并朝之移动。
        进入之前 应该确保当前朝向能识别到内容，本操作不会旋转太多去找识别目标
        停下来的条件有
        - 识别不到可交互内容
        - 可交互(单行文本)
        - 进行了交互
        :param ctx: 上下文
        :param interact_class: 需要交互的类型
        :param interact_word: 交互文本
        :param interact_during_move: 移动过程中不断尝试交互 开启后不会再使用OCR判断是否有可交互的文本。使用前需满足 1.移动时任何交互都能接受 2.交互后不在大世界
        """
        super().__init__(ctx,
                         op_name=gt(f'向 {interact_class} 移动', 'ui'),
                         timeout_seconds=20,  # 理论上移动目标都比较近 不可能20秒还没有到达
                         )

        self.no_detect_times: int = 0
        """没有识别的次数"""

        self.start_move_time: float = 0
        """开始移动的时间"""

        self.interact_class: str = interact_class
        """需要交互的类型"""

        self.interact_word: str = interact_word
        """交互文本"""

        self.interact_during_move: bool = interact_during_move
        """移动过程中不断尝试交互"""

    def _init_before_execute(self):
        super()._init_before_execute()

        self.existed_interact_word: Optional[str] = None
        """还没开始移动就已经存在的交互词"""

    def _execute_one_round(self) -> OperationOneRoundResult:
        now = time.time()
        screen = self.screenshot()

        if self.existed_interact_word is None:
            self._check_interact_word(screen)

        if self.interact_during_move:  # 只有不断交互的情况 可能会进入不在大世界的页面
            in_world = screen_state.is_normal_in_world(screen, self.ctx.im)
        else:
            in_world = True

        if in_world:
            return self.handle_in_world(screen, now)
        else:
            return self.handle_not_in_world(screen, now)

    def handle_in_world(self, screen: MatLike, now: float) -> Optional[OperationOneRoundResult]:
        """
        处理在大世界的情况
        :param screen: 游戏画面
        :param now: 当前时间
        :return:
        """
        need_ocr = len(self.existed_interact_word) > 0 or not self.interact_during_move

        if not need_ocr:
            self.ctx.controller.interact(
                pos=ScreenNormalWorld.MOVE_INTERACT_SINGLE_LINE.value.center,
                interact_type=GameController.MOVE_INTERACT_TYPE
            )

        # 移动2秒后 如果丢失了目标 停下来
        if self.ctx.controller.is_moving and now - self.start_move_time >= 2 and self.no_detect_times > 0:
            self.ctx.controller.stop_moving_forward()
            return self.round_wait()

        # 只有不直接交互的情况下 使用OCR判断是否已经到达
        if need_ocr and self._check_interact_word(screen):
            self.ctx.controller.stop_moving_forward()
            return self.round_success(status=SimUniMoveToInteractByDetect.STATUS_ARRIVAL)

        # 判断交互物体的位置
        pos_list = self.get_interact_pos(screen)
        if len(pos_list) == 0:
            return self.handle_no_detect()
        else:
            return self.handle_detect(pos_list)

    def get_interact_pos(self, screen: MatLike) -> List[DetectObjectResult]:
        """
        识别画面中交互物体的位置
        :param screen: 游戏截图
        :return:
        """
        frame_result = self.ctx.yolo_detector.sim_uni_yolo.detect(screen)
        filter_results = []
        for result in frame_result.results:
            if not result.detect_class.class_cate == self.interact_class:
                continue
            filter_results.append(result)
        if self.ctx.one_dragon_config.is_debug:
            cv2_utils.show_image(draw_detections(frame_result), win_name='SimUniMoveToInteractByDetect')
        return filter_results

    def handle_no_detect(self) -> OperationOneRoundResult:
        """
        处理当前画面识别不到交互物体的情况
        :return:
        """
        self.no_detect_times += 1

        if self.no_detect_times >= 9:
            return self.round_fail(SimUniMoveToInteractByDetect.STATUS_NO_DETECT)

        # 第一次向右转一点 后续就在固定范围内晃动
        if self.no_detect_times == 1:
            angle = 15
        else:
            angle = -30 if self.no_detect_times % 2 == 0 else 30

        self.ctx.controller.turn_by_angle(angle)
        return self.round_wait(SimUniMoveToInteractByDetect.STATUS_NO_DETECT, wait=0.5)

    def handle_detect(self, pos_list: List[DetectObjectResult]) -> OperationOneRoundResult:
        """
        处理有交互物体的情况
        :param pos_list: 识别的列表
        :return:
        """
        self.no_detect_times = 0
        target = pos_list[0]  # 先固定找第一个
        target_angle = delta_angle_to_detected_object(target)
        log.debug('目标角度 %.2f', target_angle)
        turn_angle = turn_by_angle_slowly(self.ctx, target_angle)
        if abs(target_angle) >= _MAX_TURN_ANGLE * 2:  # 转向较大时 先完成转向再开始移动
            return self.round_wait()
        self.ctx.controller.start_moving_forward()
        self.start_move_time = time.time()
        return self.round_wait()

    def handle_not_in_world(self, screen: MatLike, now: float) -> Optional[OperationOneRoundResult]:
        """
        处理不在大世界的情况 暂时只有交互成功会进入
        :param screen: 游戏画面
        :param now: 当前时间
        :return:
        """
        self.ctx.controller.stop_moving_forward()
        return self.round_success(status=SimUniMoveToInteractByDetect.STATUS_INTERACT)

    def _after_operation_done(self, result: OperationResult):
        """
        无论以哪种方式结束 都停止移动
        :param result:
        :return:
        """
        super()._after_operation_done(result)
        self.ctx.controller.stop_moving_forward()

    def _check_interact_word(self, screen: MatLike) -> bool:
        """
        识别当前画面的交互文本
        :param screen:
        :return: 是否符合目标 可以交互
        """
        words = get_move_interact_words(self.ctx, screen, single_line=True)
        self.existed_interact_word = words[0].data if len(words) > 0 else ''
        log.debug('移动前已有交互 %s', self.existed_interact_word)
        is_target = self._is_target_interact()
        if is_target:  # 符合目标交互 就不需要OCR了
            self.existed_interact_word = ''

        return is_target

    def _is_target_interact(self) -> bool:
        return (
                len(self.existed_interact_word) > 0
                and str_utils.find_by_lcs(self.existed_interact_word, gt(self.interact_word, 'ocr'), percent=0.1)
        )


class MoveToNextLevelV2(MoveToNextLevel):

    def __init__(self, ctx: Context,
                 level_type: SimUniLevelType):
        """
        朝下一层入口走去 并且交互
        需确保不会被其它内容打断
        :param ctx:
        :param level_type: 当前楼层的类型 精英层的话 有可能需要确定
        """
        super().__init__(ctx,
                         level_type=level_type,
                         random_turn=False
                         )

    def _init_before_execute(self):
        super()._init_before_execute()

        self.existed_interact_word: str = ''
        """还没开始移动就已经存在的交互词"""

        self.find_entry: bool = False
        """是否找到了下层入口"""

    def _turn_to_next(self) -> OperationOneRoundResult:
        """
        寻找下层入口 并转向
        :return:
        """
        screen = self.screenshot()

        words = get_move_interact_words(self.ctx, screen, single_line=True)
        self.existed_interact_word = words[0].data if len(words) > 0 and len(words[0].data) > 0 else ''
        if len(self.existed_interact_word) > 0:
            log.debug('开始朝下层入口移动前已有交互 %s', self.existed_interact_word)
        if self._is_target_interact():  # 符合目标交互 就不需要OCR了
            self.existed_interact_word = ''

        frame_result = self.ctx.yolo_detector.sim_uni_yolo.detect(screen)

        entry_angles: List[float] = []
        for result in frame_result.results:
            delta_angle = delta_angle_to_detected_object(result)
            if result.detect_class.class_cate == '模拟宇宙下层入口':
                entry_angles.append(delta_angle)

        if len(entry_angles) > 0:
            avg_delta_angle = np.mean(entry_angles)
            log.debug('转向 %.2f', avg_delta_angle)
            turn_by_angle_slowly(self.ctx, avg_delta_angle)
            return self.round_success(wait=0.1)
        else:
            self.ctx.controller.turn_by_angle(35)
            return self.round_retry(status=MoveToNextLevel.STATUS_ENTRY_NOT_FOUND, wait=0.5)

    def _move_and_interact(self) -> OperationOneRoundResult:
        now = time.time()

        # 等待最开始的交互词消失了 就可以无脑交互了
        need_ocr: bool = len(self.existed_interact_word) > 0
        log.debug('是否需要OCR %s', need_ocr)
        if not need_ocr:
            self.ctx.controller.interact(
                pos=ScreenNormalWorld.MOVE_INTERACT_SINGLE_LINE.value.center,
                interact_type=GameController.MOVE_INTERACT_TYPE
            )

        screen = self.screenshot()

        in_world = screen_state.is_normal_in_world(screen, self.ctx.im)

        if not in_world:
            # 如果已经不在大世界画了 就认为成功了
            return self.round_success()

        if self.is_moving:
            if now - self.start_move_time > MoveToNextLevel.MOVE_TIME:
                self.ctx.controller.stop_moving_forward()
                self.is_moving = False
            elif need_ocr:
                interact = self._try_interact(screen)
                if interact is not None:
                    return interact
            return self.round_wait()
        else:
            type_list = MoveToNextLevel.get_next_level_type(screen, self.ctx.ih)
            if len(type_list) == 0:  # 当前没有入口 随便旋转看看
                if self.random_turn:
                    # 因为前面已经转向了入口 所以就算被遮挡 只要稍微转一点应该就能看到了
                    angle = (25 + 10 * self.op_round) * (1 if self.op_round % 2 == 0 else -1)  # 来回转动视角
                else:
                    angle = 35
                self.ctx.controller.turn_by_angle(angle)
                return self.round_retry(MoveToNextLevel.STATUS_ENTRY_NOT_FOUND, wait=1)

            target = MoveToNextLevel.get_target_entry(type_list, self.config)

            self._move_towards(target)
            return self.round_wait(wait=0.1)

    def _can_interact(self, screen: MatLike) -> bool:
        """
        当前是否可以交互
        :param screen: 屏幕截图
        :return:
        """
        words = get_move_interact_words(self.ctx, screen, single_line=True)
        self.existed_interact_word = words[0].data if len(words) > 0 and len(words[0].data) > 0 else ''
        return self._is_target_interact()

    def _is_target_interact(self) -> bool:
        return (
                len(self.existed_interact_word) > 0
                and str_utils.find_by_lcs(self.existed_interact_word, gt('区域', 'ocr'), percent=0.1)
        )

    def _after_operation_done(self, result: OperationResult):
        super()._after_operation_done(result)
        self.ctx.controller.stop_moving_forward()

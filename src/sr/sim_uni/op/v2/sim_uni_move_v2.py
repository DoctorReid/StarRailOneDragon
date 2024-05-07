import time
from typing import List, Optional, ClassVar

from cv2.typing import MatLike

from basic import Point, cal_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.const import game_config_const
from sr.context import Context
from sr.control import GameController
from sr.image.sceenshot import mini_map, MiniMapInfo, screen_state
from sr.operation import Operation, OperationOneRoundResult
from sr.operation.unit.interact import check_move_interact
from sr.operation.unit.move import GetRidOfStuck
from sr.screen_area.screen_normal_world import ScreenNormalWorld
from sr.sim_uni.op.sim_uni_battle import SimUniEnterFight
from sryolo.detector import DetectResult, draw_detections


_MAX_TURN_ANGLE = 15  # 由于目标识别没有纵深 判断的距离方向不准 限定转向角度慢慢转过去


def delta_angle_to_detected_object(obj: DetectResult) -> float:
    """
    转向识别物体需要的偏移角度
    :param obj:
    :return: 偏移角度 正数往右转 负数往左转
    """
    character_pos = Point(960, 920)  # 人物脚底
    obj_pos = Point((obj.x1 + obj.x2) / 2, obj.y2)  # 识别框底部

    # 小地图用的角度 正右方为0 顺时针为正
    mm_angle = cal_utils.get_angle_by_pts(character_pos, obj_pos)

    # 与画面正前方的偏移角度 就是需要转的角度
    turn_angle = mm_angle - 270

    # 由于目前没有距离的推测 不要一次性转太多角度
    if turn_angle > _MAX_TURN_ANGLE:
        turn_angle = _MAX_TURN_ANGLE
    if turn_angle < -_MAX_TURN_ANGLE:
        turn_angle = -_MAX_TURN_ANGLE

    return turn_angle


def turn_to_detected_object(ctx: Context, obj: DetectResult) -> float:
    """
    转向一个识别到的物体
    :param ctx: 上下文
    :param obj: 检测物体
    :return: 转向角度 正数往右转 负数往左转
    """
    turn_angle = delta_angle_to_detected_object(obj)
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

        mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
        mm_info: MiniMapInfo = mini_map.analyse_mini_map(mm)

        if not self.no_attack and mini_map.is_under_attack_new(mm_info, danger=True, enemy=True):
            return self._enter_battle()

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
            return Operation.round_wait()

        # 新距离比旧距离大 大概率已经到了一个点了 捕捉到的是第二个点
        if len(self.dis) > 0 and dis - self.dis[-1] > 10:
            return self._arrive()

        self.dis.append(dis)
        self.last_rec_time = now

        if len(self.dis) > SimUniMoveToEnemyByMiniMap.DIS_MAX_LEN:
            self.dis.pop(0)

        self.ctx.controller.move_towards(self.current_pos, pos, angle,
                                         run=self.ctx.game_config.run_mode != game_config_const.RUN_MODE_OFF)
        return Operation.round_wait()

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
                return Operation.round_fail('脱困失败')
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
            return Operation.round_success(SimUniMoveToEnemyByMiniMap.STATUS_FIGHT)
        else:
            return Operation.round_by_op(op_result)

    def _arrive(self) -> OperationOneRoundResult:
        """
        到达红点后处理
        :return:
        """
        if self.stop_after_arrival:
            self.ctx.controller.stop_moving_forward()
        return Operation.round_success(SimUniMoveToEnemyByMiniMap.STATUS_ARRIVAL)


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
                         op_name=gt('向怪物移动', 'ui'))

        self.no_enemy_times: int = 0  # 没有发现敌人的次数
        self.start_move_time: float = 0  # 开始移动的时间

    def _execute_one_round(self) -> OperationOneRoundResult:
        stuck = self.move_in_stuck()  # 先尝试脱困 再进行移动
        if stuck is not None:  # 只有脱困失败的时候会有返回结果
            return stuck

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
            return Operation.round_wait()

        # 进行目标识别判断后续动作
        return self.detect_screen(screen)

    def move_in_stuck(self) -> Optional[OperationOneRoundResult]:
        """
        判断是否被困且进行移动
        :return: 如果被困次数过多就返回失败
        """
        # 暂时未知道怎么判断
        return None

    def enter_battle(self) -> OperationOneRoundResult:
        """
        进入战斗
        :return:
        """
        op = SimUniEnterFight(self.ctx)
        op_result = op.execute()
        if op_result.success:
            return Operation.round_success(SimUniMoveToEnemyByDetect.STATUS_FIGHT)
        else:
            return Operation.round_by_op(op_result)

    def detect_screen(self, screen: MatLike) -> OperationOneRoundResult:
        """
        对画面进行识别 根据结果进行后续判断
        :param screen:
        :return:
        """
        self.ctx.init_yolo()
        detect_result = self.ctx.yolo.detect(screen)
        normal_enemy_result = []
        can_attack: bool = False
        for result in detect_result:
            if result.detect_class.class_cate == '普通怪':
                normal_enemy_result.append(result)
            elif result.detect_class.class_cate in ['界面提示被锁定', '界面提示可攻击']:
                can_attack = True

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
            return Operation.round_fail(SimUniMoveToEnemyByDetect.STATUS_NO_ENEMY)

        # 第一次向右转一点 后续就在固定范围内晃动
        if self.no_enemy_times == 1:
            angle = 15
        else:
            angle = -30 if self.no_enemy_times % 2 == 0 else 30

        self.ctx.controller.turn_by_angle(angle)
        return Operation.round_wait(SimUniMoveToEnemyByDetect.STATUS_NO_ENEMY, wait=0.5)

    def handle_enemy(self, enemy_pos_list: List[DetectResult]) -> OperationOneRoundResult:
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
        return Operation.round_wait()

    def show_enemy(self, screen: MatLike, enemy_pos_list: List[DetectResult]):
        if not self.ctx.one_dragon_config.is_debug:
            return
        img = draw_detections(screen, enemy_pos_list)
        cv2_utils.show_image(img, win_name='SimUniMoveToEnemyByDetect')


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
                         op_name=gt(f'向 {interact_class} 移动', 'ui'))

        self.no_detect_times: int = 0  # 没有识别的次数
        self.start_move_time: float = 0  # 开始移动的时间
        self.interact_class: str = interact_class  # 需要交互的类型
        self.interact_word: str = interact_word  # 交互文本
        self.interact_during_move: bool = interact_during_move  # 移动过程中不断尝试交互

    def _execute_one_round(self) -> OperationOneRoundResult:
        now = time.time()
        screen = self.screenshot()

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
        if self.interact_during_move:
            self.ctx.controller.interact(
                pos=ScreenNormalWorld.MOVE_INTERACT_SINGLE_LINE.value.center,
                interact_type=GameController.MOVE_INTERACT_TYPE
            )

        stuck = self.move_in_stuck()  # 先尝试脱困 再进行移动
        if stuck is not None:  # 只有脱困失败的时候会有返回结果
            return stuck

        # 移动2秒后 如果丢失了目标 停下来
        if self.ctx.controller.is_moving and now - self.start_move_time >= 2 and self.no_detect_times > 0:
            self.ctx.controller.stop_moving_forward()
            return Operation.round_wait()

        # 只有不直接交互的情况下 使用OCR判断是否已经到达
        if not self.interact_during_move and self.can_interact(screen):
            self.ctx.controller.stop_moving_forward()
            return Operation.round_success(status=SimUniMoveToInteractByDetect.STATUS_ARRIVAL)

        # 判断交互物体的位置
        pos_list = self.get_interact_pos(screen)
        if len(pos_list) == 0:
            return self.handle_no_detect()
        else:
            self.show_detect(screen, pos_list)
            return self.handle_detect(pos_list)

    def move_in_stuck(self) -> Optional[OperationOneRoundResult]:
        """
        判断是否被困且进行移动
        :return: 如果被困次数过多就返回失败
        """
        # 暂时未知道怎么判断
        return None

    def get_interact_pos(self, screen: MatLike) -> List[DetectResult]:
        """
        识别画面中交互物体的位置
        :param screen: 游戏截图
        :return:
        """
        self.ctx.init_yolo()
        detect_results = self.ctx.yolo.detect(screen)
        filter_results = []
        for result in detect_results:
            if not result.detect_class.class_cate == self.interact_class:
                continue
            filter_results.append(result)
        return filter_results

    def handle_no_detect(self) -> OperationOneRoundResult:
        """
        处理当前画面识别不到交互物体的情况
        :return:
        """
        self.no_detect_times += 1
        if self.no_detect_times >= 9:
            return Operation.round_fail(SimUniMoveToInteractByDetect.STATUS_NO_DETECT)

        # 第一次向右转一点 后续就在固定范围内晃动
        if self.no_detect_times == 1:
            angle = 15
        else:
            angle = -30 if self.no_detect_times % 2 == 0 else 30

        self.ctx.controller.turn_by_angle(angle)
        return Operation.round_wait(SimUniMoveToInteractByDetect.STATUS_NO_DETECT, wait=0.5)

    def handle_detect(self, pos_list: List[DetectResult]) -> OperationOneRoundResult:
        """
        处理有交互物体的情况
        :param pos_list: 识别的列表
        :return:
        """
        self.no_detect_times = 0
        target = pos_list[0]  # 先固定找第一个
        turn_angle = turn_to_detected_object(self.ctx, target)
        if abs(turn_angle) >= _MAX_TURN_ANGLE:  # 转向较大时 先完成转向再开始移动
            return Operation.round_wait()
        self.ctx.controller.start_moving_forward()
        self.start_move_time = time.time()
        return Operation.round_wait()

    def show_detect(self, screen: MatLike, enemy_pos_list: List[DetectResult]):
        if not self.ctx.one_dragon_config.is_debug:
            return
        img = draw_detections(screen, enemy_pos_list)
        cv2_utils.show_image(img, win_name='SimUniMoveToInteractByDetect')

    def can_interact(self, screen) -> bool:
        """
        当前可交互
        :return:
        """
        interact_pos = check_move_interact(self.ctx, screen, self.interact_word, single_line=True)
        return interact_pos is not None

    def handle_not_in_world(self, screen: MatLike, now: float) -> Optional[OperationOneRoundResult]:
        """
        处理不在大世界的情况 暂时只有交互成功会进入
        :param screen: 游戏画面
        :param now: 当前时间
        :return:
        """
        self.ctx.controller.stop_moving_forward()
        return Operation.round_success(status=SimUniMoveToInteractByDetect.STATUS_INTERACT)

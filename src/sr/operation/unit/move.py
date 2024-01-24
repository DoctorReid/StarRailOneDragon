import time
from typing import List, Optional, Tuple, Callable, ClassVar, Union

import cv2
import numpy as np

from cv2.typing import MatLike

from basic import Point, cal_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr import cal_pos
from sr.config import game_config
from sr.const import map_const, game_config_const
from sr.const.map_const import Region
from sr.context import Context
from sr.control import GameController
from sr.image.sceenshot import mini_map, MiniMapInfo, LargeMapInfo, large_map, screen_state
from sr.operation import Operation, OperationOneRoundResult, OperationResult
from sr.operation.unit.enter_auto_fight import EnterAutoFight


class GetRidOfStuck(Operation):

    def __init__(self, ctx: Context, stuck_times: int):
        """
        简单的脱困指令
        返回数据为脱困使用的时间
        以下方式各尝试2遍
        1. 往左 然后往前走
        2. 往右 然后往前走
        3. 往后再往左 然后往前走
        4. 往后再往右 然后往前走
        5. 往左再往后再往右 然后往前走
        6. 往右再往后再往左 然后往前走
        :param ctx:
        :param stuck_times: 被困次数 1~12
        """
        super().__init__(ctx, op_name='%s %d' % (gt('尝试脱困', 'ui'), stuck_times))
        self.stuck_times: int = stuck_times

    def _execute_one_round(self) -> OperationOneRoundResult:
        ctrl: GameController = self.ctx.controller

        ctrl.stop_moving_forward()

        move_unit_sec = 0.25
        try_move_unit = self.stuck_times % 2 if self.stuck_times % 2 != 0 else 2
        try_method = (self.stuck_times + 1) // 2

        if try_method == 1:  # 左 前
            walk_sec = try_move_unit * move_unit_sec
            ctrl.move('a', walk_sec)
            ctrl.start_moving_forward()  # 多往前走1秒再判断是否被困
            time.sleep(1)
            total_time = walk_sec + 1
        elif try_method == 2:  # 右 前
            walk_sec = try_move_unit * move_unit_sec
            ctrl.move('d', walk_sec)
            ctrl.start_moving_forward()
            time.sleep(1)
            total_time = walk_sec + 1
        elif try_method == 3:  # 后左 前
            walk_sec = try_move_unit * move_unit_sec
            ctrl.move('s', walk_sec)
            ctrl.move('a', walk_sec)
            ctrl.move('w', walk_sec)
            ctrl.start_moving_forward()
            time.sleep(1)
            total_time = walk_sec * 3 + 1
        elif try_method == 4:  # 后右 前
            walk_sec = try_move_unit * move_unit_sec
            ctrl.move('s', walk_sec)
            ctrl.move('d', walk_sec)
            ctrl.move('w', walk_sec)
            ctrl.start_moving_forward()
            time.sleep(1)
            total_time = walk_sec * 3 + 1
        elif try_method == 5:  # 左后右 前
            walk_sec = try_move_unit * move_unit_sec
            ctrl.move('a', walk_sec)
            ctrl.move('s', walk_sec)
            ctrl.move('d', walk_sec + move_unit_sec)
            ctrl.start_moving_forward()
            time.sleep(1)
            total_time = walk_sec * 3 + move_unit_sec + 1
        elif try_method == 6:  # 右后左 前
            walk_sec = try_move_unit * move_unit_sec
            ctrl.move('d', walk_sec)
            ctrl.move('s', walk_sec)
            ctrl.move('a', walk_sec + move_unit_sec)
            ctrl.start_moving_forward()
            time.sleep(1)
            total_time = walk_sec * 3 + move_unit_sec + 1
        else:
            total_time = 0

        return Operation.round_success(data=total_time)


class MoveDirectly(Operation):
    """
    从当前位置 朝目标点直线前行
    有简单的脱困功能
    """
    max_len: int = 6  # 最多存储多少个走过的坐标
    rec_pos_interval: float = 0.5  # 间隔多少秒记录一次坐标
    stuck_distance: float = 20  # 移动距离多少以内认为是被困
    arrival_distance: float = 10  # 多少距离内认为是到达目的地
    fail_after_no_battle: float = 120  # 多少秒无战斗后退出 通常不会有路线这么久都遇不到怪 只能是卡死了 然后脱困算法又让角色产生些位移

    def __init__(self, ctx: Context,
                 lm_info: LargeMapInfo,
                 start: Point,
                 target: Point,
                 next_lm_info: Optional[LargeMapInfo] = None,
                 stop_afterwards: bool = True,
                 no_run: bool = False,
                 no_battle: bool = False,
                 op_callback: Optional[Callable[[OperationResult], None]] = None):
        super().__init__(ctx, op_name=gt('移动 %s -> %s') % (start, target), op_callback=op_callback)
        self.lm_info: LargeMapInfo = lm_info
        self.next_lm_info: LargeMapInfo = next_lm_info
        self.region: Region = lm_info.region
        self.target: Point = target
        self.start_pos: Point = start
        self.pos: List[Point] = []
        self.stuck_times = 0  # 被困次数
        self.last_rec_time = 0  # 上一次记录坐标的时间
        self.no_pos_times = 0  # 累计算不到坐标的次数
        self.stop_afterwards = stop_afterwards  # 最后是否停止前进
        self.last_auto_fight_fail: bool = False  # 上一次索敌是否失败 只有小地图背景污染严重时候出现
        self.last_battle_time = time.time()
        self.last_no_pos_time = 0  # 上一次算不到坐标的时间 目前算坐标太快了 可能地图还在缩放中途就已经失败 所以稍微隔点时间再记录算不到坐标

        self.run_mode = game_config_const.RUN_MODE_OFF if no_run else game_config.get().run_mode
        self.no_battle: bool = no_battle  # 本次移动是否没有战斗

    def _init_before_execute(self):
        super()._init_before_execute()
        now = time.time()
        self.last_rec_time = now - 1
        self.last_battle_time = now
        self.pos = []
        if self.ctx.controller.is_moving:  # 连续移动的时候 使用开始点作为一个起始点
            self.pos.append(self.start_pos)

    def _execute_one_round(self) -> OperationOneRoundResult:
        stuck = self.move_in_stuck()  # 先尝试脱困 再进行移动
        if stuck is not None:
            return stuck

        # 如果使用小箭头计算方向 则需要前进一步 保证小箭头方向就是人物朝向
        # if not self.ctx.controller.is_moving:
        #     self.ctx.controller.move('w')
        #     time.sleep(0.5)  # 等待人物转过来再截图
        now_time = time.time()

        if not self.no_battle and now_time - self.last_battle_time > MoveDirectly.fail_after_no_battle:
            return Operation.round_fail('移动超时')

        screen = self.screenshot()



        be_attacked = self.be_attacked(screen)  # 查看是否被攻击
        if be_attacked is not None:
            return be_attacked

        mm = mini_map.cut_mini_map(screen)

        check_enemy = self.check_enemy_and_attack(mm)  # 根据小地图判断是否被怪锁定 是的话停下来处理敌人
        if check_enemy is not None:
            return check_enemy

        next_pos, mm_info = self.cal_pos(mm, now_time)  # 计算当前坐标

        check_no_pos = self.check_no_pos(next_pos, now_time)  # 坐标计算失败处理
        if check_no_pos is not None:
            return check_no_pos

        check_arrive = self.check_arrive(next_pos)  # 判断是否到达
        if check_arrive is not None:
            return check_arrive

        self.move(next_pos, now_time, mm_info)

        return Operation.round_wait()

    def move_in_stuck(self) -> Optional[OperationOneRoundResult]:
        """
        判断是否被困且进行移动
        :return: 如果被困次数过多就返回失败
        """
        if len(self.pos) == 0:
            return None

        first_pos = self.pos[0]
        last_pos = self.pos[len(self.pos) - 1]

        # 通过第一个坐标和最后一个坐标的距离 判断是否困住了
        if len(self.pos) >= MoveDirectly.max_len and \
                cal_utils.distance_between(first_pos, last_pos) < MoveDirectly.stuck_distance:
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
            self.last_auto_fight_fail = False
            self.ctx.controller.stop_moving_forward()
            fight = EnterAutoFight(self.ctx)
            fight_result = fight.execute()
            if not fight_result.success:
                return Operation.round_fail(status=fight_result.status, data=fight_result.data)
            self.last_battle_time = time.time()
            self.last_rec_time = time.time()  # 战斗可能很久 需要重置一下记录坐标时间
            return Operation.round_wait()
        return None

    def check_enemy_and_attack(self, mm: MatLike) -> Optional[OperationOneRoundResult]:
        """
        从小地图检测敌人 如果有的话 进入索敌
        :param mm:
        :return: 是否有敌人
        """
        if self.no_battle:
            return None
        if self.last_auto_fight_fail:  # 上一次索敌失败了 可能小地图背景有问题 等待下一次进入战斗画面刷新
            return None
        if not mini_map.is_under_attack(mm, game_config.get().mini_map_pos):
            return None
        self.ctx.controller.stop_moving_forward()  # 先停下来再攻击
        fight = EnterAutoFight(self.ctx)
        op_result = fight.execute()
        if not op_result.success:
            return Operation.round_fail(status=op_result.status, data=op_result.data)
        self.last_auto_fight_fail = (op_result.status == EnterAutoFight.STATUS_ENEMY_NOT_FOUND)
        self.last_battle_time = time.time()
        self.last_rec_time = time.time()  # 战斗可能很久 需要重置一下记录坐标时间

        return Operation.round_wait()

    def cal_pos(self, mm: MatLike, now_time: float) -> Tuple[Optional[Point], MiniMapInfo]:
        """
        根据上一次的坐标和行进距离 计算当前位置坐标
        :param mm: 小地图截图
        :param now_time: 当前时间
        :return:
        """
        # 根据上一次的坐标和行进距离 计算当前位置
        if self.last_rec_time > 0:
            move_time = now_time - self.last_rec_time
            if move_time < 1:
                move_time = 1
        else:
            move_time = 1
        move_distance = self.ctx.controller.cal_move_distance_by_time(move_time, run=self.run_mode != game_config_const.RUN_MODE_OFF)
        last_pos = self.pos[len(self.pos) - 1] if len(self.pos) > 0 else self.start_pos
        possible_pos = (last_pos.x, last_pos.y, move_distance)
        log.debug('准备计算人物坐标 使用上一个坐标为 %s 移动时间 %.2f 是否在移动 %s', possible_pos,
                  move_time, self.ctx.controller.is_moving)
        lm_rect = large_map.get_large_map_rect_by_pos(self.lm_info.gray.shape, mm.shape[:2], possible_pos)

        sp_map = map_const.get_sp_type_in_rect(self.region, lm_rect)
        mm_info = mini_map.analyse_mini_map(mm, self.ctx.im, sp_types=set(sp_map.keys()))

        if len(self.pos) == 0:
            return self.start_pos, mm_info

        next_pos = cal_pos.cal_character_pos(self.ctx.im, self.lm_info, mm_info, lm_rect=lm_rect,
                                             retry_without_rect=False, running=self.ctx.controller.is_moving)
        if next_pos is None and self.next_lm_info is not None:
            next_pos = cal_pos.cal_character_pos(self.ctx.im, self.next_lm_info, mm_info, lm_rect=lm_rect,
                                                 retry_without_rect=False, running=self.ctx.controller.is_moving)
        if next_pos is None:
            log.error('无法判断当前人物坐标 使用上一个坐标为 %s 移动时间 %.2f 是否在移动 %s', possible_pos, move_time,
                      self.ctx.controller.is_moving)
        return next_pos, mm_info

    def check_no_pos(self, next_pos: Point, now_time: float) -> Optional[OperationOneRoundResult]:
        """
        并判断是否识别不到坐标
        过长时间无法识别需要停止角色移动 甚至错误退出
        :param next_pos: 计算得到的坐标
        :param now_time: 当前时间
        :return:
        """
        if next_pos is None:
            if now_time - self.last_no_pos_time > 0.5:
                self.no_pos_times += 1
                self.last_no_pos_time = now_time
                if self.no_pos_times >= 3:  # 不要再乱走了
                    self.ctx.controller.stop_moving_forward()
                if self.no_pos_times >= 10:
                    return Operation.round_fail('无法识别坐标')
            return Operation.round_wait()
        else:
            self.no_pos_times = 0

    def check_arrive(self, next_pos: Point) -> Optional[OperationOneRoundResult]:
        """
        检查是否已经到达目标点
        :param next_pos:
        :return:
        """
        if cal_utils.distance_between(next_pos, self.target) < MoveDirectly.arrival_distance:
            if self.stop_afterwards:
                self.ctx.controller.stop_moving_forward()
            return Operation.round_success(data=next_pos)
        return None

    def move(self, next_pos: Point, now_time: float, mm_info: MiniMapInfo):
        """
        移动
        :param next_pos:
        :param now_time:
        :param mm_info:
        :return:
        """
        if now_time - self.last_rec_time > self.rec_pos_interval:  # 隔一段时间才记录一个点
            self.ctx.controller.move_towards(next_pos, self.target, mm_info.angle,
                                             run=self.run_mode == game_config_const.RUN_MODE_BTN)
            # time.sleep(0.5)  # 如果使用小箭头计算方向 则需要等待人物转过来再进行下一轮
            self.pos.append(next_pos)
            log.debug('记录坐标 %s', next_pos)
            if len(self.pos) > MoveDirectly.max_len:
                del self.pos[0]
            self.last_rec_time = now_time

    def on_pause(self):
        super().on_pause()
        self.ctx.controller.stop_moving_forward()

    def on_resume(self):
        super().on_resume()
        self.last_rec_time += self.current_pause_time
        self.last_battle_time += self.current_pause_time


class MoveToEnemy(Operation):

    STATUS_ENEMY_NOT_FOUND: ClassVar[str] = '未找到敌人'

    def __init__(self, ctx: Context, no_run: bool = False, timeout_seconds: float = 600):
        """
        按小地图上的红色点 向敌人移动
        适合只有一个怪的场景
        - 忘却之庭
        - 模拟宇宙精英怪
        :param ctx: 上下文
        :param no_run: 不能疾跑
        :param timeout_seconds: 超时时间
        """
        super().__init__(ctx, op_name=gt('向敌人移动', 'ui'), timeout_seconds=timeout_seconds)
        self.run_mode = game_config_const.RUN_MODE_OFF if no_run else game_config.get().run_mode
        self.last_move_time: float = 0  # 上一次移动的时间

    def _init_before_execute(self):
        super()._init_before_execute()
        self.last_move_time = 0

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()
        mm = mini_map.cut_mini_map(screen)
        pos = self._find_enemy_pos(mm)

        if pos is None:
            return Operation.round_retry(MoveToEnemy.STATUS_ENEMY_NOT_FOUND, wait=1)

        center = Point(mm.shape[1] // 2, mm.shape[0] // 2)

        if pos is None or cal_utils.distance_between(pos, center) < 20:  # 已经到达
            self.ctx.controller.stop_moving_forward()
            return Operation.round_success()
        elif pos is not None:  # 朝目标走去
            now = time.time()
            if now - self.last_move_time > 0.5:  # 隔一段时间再调整方向移动
                self.last_enemy_pos = pos
                _, _, angle = mini_map.analyse_arrow_and_angle(mm, self.ctx.im)
                self.ctx.controller.move_towards(center, pos, angle,
                                                 run=self.run_mode == game_config_const.RUN_MODE_BTN)
            return Operation.round_wait()
        else:  # 不应该有这种情况
            return Operation.round_retry('unknown')

    def _find_enemy_pos(self, mm: Optional[MatLike] = None) -> Optional[Point]:
        """
        在小地图上找到敌人红点的位置
        目前只能处理一个红点的情况
        :param mm: 小地图图片
        :return: 红点位置
        """
        if mm is None:
            screen = self.screenshot()
            mm = mini_map.cut_mini_map(screen)

        _, _, angle = mini_map.analyse_arrow_and_angle(mm, self.ctx.im)
        to_del = mini_map.get_radio_to_del(self.ctx.im, angle)

        mm2 = mini_map.remove_radio(mm, to_del)
        # cv2_utils.show_image(mm2, win_name='mm2')

        lower_color = np.array([0, 0, 150], dtype=np.uint8)
        upper_color = np.array([60, 60, 255], dtype=np.uint8)
        red_part = cv2.inRange(mm2, lower_color, upper_color)
        # cv2_utils.show_image(red_part, win_name='red_part')

        # 膨胀一下找连通块
        to_check = cv2_utils.dilate(red_part, 5)
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(to_check, connectivity=8)

        if num_labels <= 1:  # 没有连通块 走到敌人附近了
            return None

        # 找到最大的连通区域
        largest_label = 1
        max_area = stats[largest_label, cv2.CC_STAT_AREA]
        for label in range(2, num_labels):
            area = stats[label, cv2.CC_STAT_AREA]
            if area > max_area:
                max_area = area
                largest_label = label

        # 找到最大连通区域的中心点
        center_x = int(centroids[largest_label, 0])
        center_y = int(centroids[largest_label, 1])

        return Point(center_x, center_y)


class MoveForward(Operation):

    def __init__(self, ctx: Context, seconds: float):
        """
        向前走一段时间
        :param ctx:
        :param seconds: 秒数
        """
        super().__init__(ctx, op_name='%s %s' %
                                      (gt('向前移动', 'ui'),
                                       gt('%.2f秒' % seconds, 'ui'))
                         )
        self.seconds: float = seconds

    def _execute_one_round(self) -> OperationOneRoundResult:
        self.ctx.controller.start_moving_forward()
        time.sleep(self.seconds)
        self.ctx.controller.stop_moving_forward()
        return Operation.round_success()


class SimplyMoveByPos(MoveDirectly):

    def __init__(self, ctx: Context,
                 lm_info: LargeMapInfo,
                 start: Point,
                 target: Point,
                 next_lm_info: Optional[LargeMapInfo] = None,
                 stop_afterwards: bool = True,
                 no_run: bool = False,
                 op_callback: Optional[Callable[[OperationResult], None]] = None):
        """
        从当前位置 朝目标点直线前行
        不考虑任何其他情况
        适合在确定不会有任何打断或困住的情况下使用
        """
        super().__init__(ctx,
                         lm_info=lm_info,
                         start=start,
                         target=target,
                         next_lm_info=next_lm_info,
                         stop_afterwards=stop_afterwards,
                         no_run=no_run,
                         op_callback=op_callback)

    def be_attacked(self, screen: MatLike) -> Optional[OperationOneRoundResult]:
        return None

    def check_enemy_and_attack(self, mm: MatLike) -> Optional[OperationOneRoundResult]:
        return None
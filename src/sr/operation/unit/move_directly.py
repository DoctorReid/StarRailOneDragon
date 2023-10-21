import time

from cv2.typing import MatLike

import basic.cal_utils
from basic import os_utils, cal_utils
from basic.img.os import save_debug_image
from basic.log_utils import log
from sr import constants, cal_pos
from sr.config.game_config import get_game_config
from sr.constants.map import Region
from sr.context import Context
from sr.control import GameController
from sr.image.sceenshot import mini_map, MiniMapInfo, LargeMapInfo, battle
from sr.image.sceenshot.large_map import get_large_map_rect_by_pos
from sr.operation import Operation
from sr.operation.unit.enter_auto_fight import EnterAutoFight


class MoveDirectly(Operation):
    """
    从当前位置 朝目标点直线前行
    有简单的脱困功能
    """
    max_len: int = 5  # 最多存储多少个走过的坐标
    rec_pos_interval: float = 0.5  # 间隔多少秒记录一次坐标
    stuck_distance: float = 20  # 移动距离多少以内认为是被困
    arrival_distance: float = 10  # 多少距离内认为是到达目的地

    def __init__(self, ctx: Context,
                 lm_info: LargeMapInfo,
                 target: tuple,
                 next_lm_info: LargeMapInfo = None,
                 start: tuple = None,
                 stop_afterwards: bool = True):
        super().__init__(ctx)
        self.lm_info: LargeMapInfo = lm_info
        self.next_lm_info: LargeMapInfo = next_lm_info
        self.region: Region = lm_info.region
        self.target = target
        self.pos = []
        if start is not None:
            self.pos.append(start)
        self.stuck_times = 0  # 被困次数
        self.last_rec_time = time.time()  # 上一次记录坐标的时间
        self.no_pos_times = 0
        self.stop_afterwards = stop_afterwards  # 最后是否停止前进

    def run(self) -> bool:
        last_pos = None if len(self.pos) == 0 else self.pos[len(self.pos) - 1]

        # 通过第一个坐标和最后一个坐标的距离 判断是否困住了
        if len(self.pos) >= MoveDirectly.max_len and \
                basic.cal_utils.distance_between(self.pos[0], self.pos[len(self.pos) - 1]) < MoveDirectly.stuck_distance:
            self.stuck_times += 1
            if self.stuck_times > 12:
                log.error('脱困失败')
                if os_utils.is_debug():
                    screen = self.screenshot()
                    save_debug_image(screen, prefix=self.__class__.__name__ + "_stuck")
                return Operation.FAIL
            walk_sec = self.get_rid_of_stuck(self.stuck_times, last_pos)
            self.last_rec_time += walk_sec
        else:
            self.stuck_times = 0

        # 如果使用小箭头计算方向 则需要前进一步 保证小箭头方向就是人物朝向
        # if not self.ctx.controller.is_moving:
        #     self.ctx.controller.move('w')
        #     time.sleep(0.5)  # 等待人物转过来再截图
        now_time = time.time()
        screen = self.screenshot()

        # 可能被怪攻击了
        if battle.IN_WORLD != battle.get_battle_status(screen, self.ctx.im):
            self.ctx.controller.stop_moving_forward()
            fight = EnterAutoFight(self.ctx)
            fight.execute()
            self.last_rec_time = time.time()  # 战斗可能很久 需要重置一下记录坐标时间
            return Operation.WAIT

        mm = mini_map.cut_mini_map(screen)
        # 根据小地图判断是否被怪锁定 是的话停下来处理敌人
        if self.check_enemy_and_attack(mm):
            self.last_rec_time = time.time()  # 战斗可能很久 需要重置一下记录坐标时间
            return Operation.WAIT

        # 根据上一次的坐标和行进距离 计算当前位置
        lx, ly = last_pos
        move_distance = self.ctx.controller.cal_move_distance_by_time(now_time - self.last_rec_time)
        possible_pos = (lx, ly, move_distance)
        lm_rect = get_large_map_rect_by_pos(self.lm_info.gray.shape, mm.shape[:2], possible_pos)

        sp_map = constants.map.get_sp_type_in_rect(self.region, lm_rect)
        mm_info = mini_map.analyse_mini_map(mm, self.ctx.im, sp_types=set(sp_map.keys()),
                                            another_floor=self.region.another_floor())

        x, y = self.get_pos(mm_info, possible_pos, lm_rect)

        if x is None or y is None:
            log.error('无法判断当前人物坐标 使用上一个坐标为%s', possible_pos)
            if os_utils.is_debug():
                save_debug_image(mm, prefix='cal_pos')
            self.no_pos_times += 1
            if self.no_pos_times >= 5:  # 不要再乱走了
                self.ctx.controller.stop_moving_forward()
            if self.no_pos_times >= 10:
                log.error('持续无法判断当前人物坐标 退出本次移动')
                self.ctx.controller.stop_moving_forward()
                return Operation.FAIL
            return Operation.WAIT
        else:
            self.no_pos_times = 0

        next_pos = (x, y)

        if basic.cal_utils.distance_between(next_pos, self.target) < MoveDirectly.arrival_distance:
            log.info('目标点已到达 %s', self.target)
            if self.stop_afterwards:
                self.ctx.controller.stop_moving_forward()
            return Operation.SUCCESS

        self.ctx.controller.move_towards(next_pos, self.target, mm_info.angle)
        # time.sleep(0.5)  # 如果使用小箭头计算方向 则需要等待人物转过来再进行下一轮

        if now_time - self.last_rec_time > self.rec_pos_interval:  # 隔一段时间才记录一个点
            self.pos.append(next_pos)
            if len(self.pos) > MoveDirectly.max_len:
                del self.pos[0]
            self.last_rec_time = now_time

        return Operation.WAIT

    def get_rid_of_stuck(self, stuck_times: int, last_pos: tuple):
        """
        尝试脱困 使用往回走 再左右移 再往前走的方法
        1-3次 往左 然后直走
        4-6次 往右 然后直走
        7-9次 往后再往左 然后直走
        10-12次 往后再往右 然后直走
        :param stuck_times: 判断困住多少次了 次数越多 往回走距离越大
        :param last_pos: 上一次位置 也就是被困的位置
        :return: 这次脱困用了多久
        """
        log.info('尝试脱困第%d次', stuck_times)
        ctrl: GameController = self.ctx.controller

        ctrl.stop_moving_forward()

        walk_sec = (stuck_times % 3 if stuck_times % 3 != 0 else 3) * 0.25

        if stuck_times <= 3:
            ctrl.move('a', walk_sec)
            ctrl.start_moving_forward()  # 多往前走1秒再判断是否被困
            time.sleep(1)
            return walk_sec + 1
        elif stuck_times <= 6:
            ctrl.move('d', walk_sec)
            ctrl.start_moving_forward()
            time.sleep(1)
            return walk_sec + 1
        elif stuck_times <= 9:
            ctrl.move('s', walk_sec)
            ctrl.move('a', walk_sec)
            ctrl.move('w', walk_sec)
            ctrl.start_moving_forward()
            time.sleep(1)
            return walk_sec * 3 + 1
        elif stuck_times <= 12:
            ctrl.move('s', walk_sec)
            ctrl.move('d', walk_sec)
            ctrl.move('w', walk_sec)
            ctrl.start_moving_forward()
            time.sleep(1)
            return walk_sec * 3 + 1

        return 0

    def get_pos(self, mm_info: MiniMapInfo, possible_pos: tuple, lm_rect: tuple):
        """
        获取当前位置、 下一步方向、 记录时间
        :param mm_info: 小地图
        :param possible_pos: 上一次的位置
        :param lm_rect: 大地图区域
        :return:
        """
        start_time = time.time()

        x, y = cal_pos.cal_character_pos(self.ctx.im, self.lm_info, mm_info, lm_rect=lm_rect, retry_without_rect=False, running=self.ctx.controller.is_moving)
        if x is None and self.next_lm_info is not None:
            x, y = cal_pos.cal_character_pos(self.ctx.im, self.next_lm_info, mm_info, lm_rect=lm_rect, retry_without_rect=False, running=self.ctx.controller.is_moving)

        log.debug('计算坐标耗时 %.4f s', time.time() - start_time)
        log.info('计算当前坐标为 (%s, %s)', x, y)

        if x is not None and possible_pos[2] > 0 and cal_utils.distance_between((x, y), possible_pos[:2]) > possible_pos[2] * 2:
            x, y = None, None
            log.info('计算位置偏离上一个位置过远 舍弃')

        return x, y

    def check_enemy_and_attack(self, mm: MatLike) -> bool:
        """
        从小地图检测敌人 如果有的话 进入索敌
        :param mm:
        :return: 是否有敌人
        """
        if not mini_map.is_under_attack(mm, get_game_config().mini_map_pos):
            return False
        # pos_list = mini_map.get_enemy_location(mini_map)
        # if len(pos_list) == 0:
        #     return False
        fight = EnterAutoFight(self.ctx)
        fight.execute()

        return True

    def on_pause(self):
        super().on_pause()
        self.ctx.controller.stop_moving_forward()

    def on_resume(self):
        super().on_resume()
        self.last_rec_time = time.time()
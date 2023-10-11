import time

from cv2.typing import MatLike

import basic.cal_utils
from basic.img import cv2_utils
from basic.img.os import save_debug_image
from basic.log_utils import log
from sr import constants
from sr.config.game_config import get_game_config
from sr.constants.map import Region
from sr.context import Context
from sr.control import GameController
from sr.image.sceenshot import mini_map, MiniMapInfo, LargeMapInfo
from sr.map_cal import MapCalculator
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

    def __init__(self, ctx: Context, large_map_info: LargeMapInfo,
                 region: Region,
                 target: tuple, start: tuple = None,
                 save_screenshot: bool = False):
        super().__init__(ctx)
        self.lm_info = large_map_info
        self.region: Region = region
        self.target = target
        self.save_screenshot = save_screenshot
        self.pos = []
        if start is not None:
            self.pos.append(start)
        self.stuck_times = 0  # 被困次数
        self.last_rec_time = time.time()  # 上一次记录坐标的时间
        self.no_pos_times = 0

    def run(self) -> bool:
        last_pos = None if len(self.pos) == 0 else self.pos[len(self.pos) - 1]

        if len(self.pos) >= MoveDirectly.max_len and \
                basic.cal_utils.distance_between(self.pos[0], self.pos[len(self.pos) - 1]) < MoveDirectly.stuck_distance:
            self.stuck_times += 1
            walk_sec = self.get_rid_of_stuck(self.stuck_times)
            self.last_rec_time += walk_sec * 2
        else:
            self.stuck_times = 0

        if not self.ctx.controller.is_moving:
            self.ctx.controller.move('w')
        now_time = time.time()
        screen = self.ctx.controller.screenshot()
        if self.save_screenshot:
            save_debug_image(screen)
        mm = self.ctx.map_cal.cut_mini_map(screen)
        if self.check_enemy_and_attack(mm):  # 处理完敌人 再重新开始下一轮寻路
            self.last_rec_time = now_time
            return Operation.WAIT

        lx, ly = last_pos
        move_distance = self.ctx.controller.cal_move_distance_by_time(now_time - self.last_rec_time)
        possible_pos = (lx, ly, move_distance)
        lm_rect = self.ctx.map_cal.get_large_map_rect_by_pos(self.lm_info.gray.shape, mm.shape[:2], possible_pos)
        sp_type_list = constants.map.get_sp_type_in_rect(self.region, lm_rect)
        mm_info = self.ctx.map_cal.analyse_mini_map(mm, sp_type_list)

        x, y = self.get_pos(mm_info, lm_rect)

        if x is None or y is None:
            log.error('无法判断当前人物坐标')
            self.no_pos_times += 1
            if self.no_pos_times >= 10:
                log.error('持续无法判断当前人物坐标 退出本次移动')
                return Operation.FAIL
            return Operation.WAIT
        else:
            self.no_pos_times = 0

        next_pos = (x, y)

        if basic.cal_utils.distance_between(next_pos, self.target) < MoveDirectly.arrival_distance:
            log.info('目标点已到达 %s', self.target)
            self.ctx.controller.stop_moving_forward()
            return Operation.SUCCESS

        self.ctx.controller.move_towards(next_pos, self.target, mm_info.angle)
        time.sleep(0.5)
        # screen = self.ctx.controller.screenshot()
        # self.ctx.controller.stop_moving_forward()
        # mm = self.ctx.map_cal.cut_mini_map(screen)
        # mm_info = self.ctx.map_cal.analyse_mini_map(mm)
        # print(mm_info.angle)
        # cv2_utils.show_image(screen, win_name='screen', wait=0)
        # return Operation.SUCCESS

        if now_time - self.last_rec_time > self.rec_pos_interval:
            self.pos.append(next_pos)
            if len(self.pos) > MoveDirectly.max_len:
                del self.pos[0]
            self.last_rec_time = now_time

        return Operation.WAIT

    def get_rid_of_stuck(self, stuck_times: int):
        """
        尝试脱困 使用往回走 再左右移 再往前走的方法
        前3秒尝试往左 后三秒尝试往右
        :param stuck_times: 判断困住多少次了 次数越多 往回走距离越大
        :return:
        """
        log.info('尝试脱困第%d次', stuck_times)
        ctrl: GameController = self.ctx.controller

        ctrl.stop_moving_forward()

        walk_sec = stuck_times if stuck_times <= 3 else stuck_times - 3  #
        turn = 'a' if stuck_times <= 3 else 'd'

        ctrl.move('s', walk_sec)
        ctrl.move(turn, walk_sec)
        ctrl.start_moving_forward()
        time.sleep(walk_sec)
        return walk_sec

    def get_pos(self, mm_info: MiniMapInfo, lm_rect: tuple):
        """
        获取当前位置、 下一步方向、 记录时间
        :param mm_info: 小地图信息
        :param lm_rect: 大地图区域
        :return:
        """
        start_time = time.time()

        x, y = self.ctx.map_cal.cal_character_pos(self.lm_info, mm_info, lm_rect=lm_rect, retry_without_rect=False)

        log.debug('截图计算坐标耗时 %.4f s', time.time() - start_time)
        log.info('计算当前坐标为 (%s, %s)', x, y)

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
        self.ctx.controller.stop_moving_forward()
        super().on_pause()

    def on_resume(self):
        self.last_rec_time = time.time()
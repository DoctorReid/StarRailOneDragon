import time

from cv2.typing import MatLike

from basic.img import cv2_utils
from basic.log_utils import log
from sr.context import Context
from sr.control import GameController
from sr.image.sceenshot import mini_map
from sr.map_cal import LargeMapInfo, MapCalculator, MiniMapInfo
from sr.operation import Operation
from sr.operation.unit.enter_auto_fight import EnterAutoFight


class MoveDirectly(Operation):
    """
    从当前位置 朝目标点直线前行
    有简单的脱困功能
    """

    def __init__(self, ctx: Context, large_map_info: LargeMapInfo,
                 target: tuple, start: tuple = None):
        self.ctx = ctx
        self.lm_info = large_map_info
        self.target = target
        self.start = start

    def execute(self) -> bool:
        max_len: int = 5  # 最多存储多少个走过的坐标
        rec_pos_interval: float = 0.5  # 间隔多少秒记录一次坐标
        stuck_distance: float = 20  # 移动距离多少以内认为是被困

        pos = []
        if self.start is not None:
            pos.append(self.start)

        stuck_times = 0  # 被困次数
        last_rec_time = time.time()  # 上一次记录坐标的时间
        no_pos_times = 0

        while True:
            last_pos = None if len(pos) == 0 else pos[len(pos) - 1]

            if len(pos) >= max_len and \
                    cv2_utils.distance_between(pos[0], pos[len(pos) - 1]) < stuck_distance:
                stuck_times += 1
                walk_sec = self.get_rid_of_stuck(stuck_times)
                last_rec_time += walk_sec * 2
            else:
                stuck_times = 0

            now_time = time.time()
            screen = self.ctx.controller.screenshot()
            mm = self.ctx.map_cal.cut_mini_map(screen)
            if self.check_enemy_and_attack(mm):  # 处理完敌人 再重新开始下一轮寻路
                last_rec_time = now_time
                continue

            mm_info = self.ctx.map_cal.analyse_mini_map(mm)

            x, y, angle = self.get_pos_and_next_angle(mm_info, now_time,
                                                      last_pos, last_rec_time)

            if x is None or y is None:
                log.error('无法判断当前人物坐标')
                no_pos_times += 1
                if no_pos_times >= 10:
                    log.error('持续无法判断当前人物坐标 退出本次移动')
                    return False
                continue
            else:
                no_pos_times = 0

            next_pos = (x, y)
            self.ctx.controller.move_towards(next_pos, self.target, mm_info.angle)

            if now_time - last_rec_time > rec_pos_interval:
                pos.append(next_pos)
                if len(pos) > max_len:
                    del pos[0]
                last_rec_time = now_time

            if cv2_utils.distance_between(next_pos, self.target):
                log.info('目标点已到达 %s', self.target)
                return True

    def get_rid_of_stuck(self, stuck_times: int):
        """
        尝试脱困 使用往回走 再左右移 再往前走的方法
        前3秒尝试往左 后三秒尝试往右
        :param stuck_times: 判断困住多少次了 次数越多 往回走距离越大
        :return:
        """
        log.info('尝试脱困第%d次', stuck_times)
        ctrl: GameController = self.ctx.controller

        ctrl.stop_moving()

        walk_sec = stuck_times if stuck_times <= 3 else stuck_times - 3  #
        turn = 'a' if stuck_times <= 3 else 'd'

        ctrl.move('s', walk_sec)
        ctrl.move(turn, walk_sec)
        ctrl.start_moving_forward()
        time.sleep(walk_sec)
        return walk_sec

    def get_pos_and_next_angle(self, mm_info: MiniMapInfo, now_time: float,
                               last_pos: tuple, last_rec_time: float):
        """
        获取当前位置、 下一步方向、 记录时间
        :param mm_info: 小地图信息
        :param now_time: 现在时间
        :param last_pos: 上一次的位置
        :param last_rec_time: 上一次记录坐标的时间
        :return:
        """
        start_time = time.time()
        ctrl: GameController = self.ctx.controller
        mc: MapCalculator = self.ctx.map_cal

        lx, ly = last_pos
        r = ctrl.cal_move_distance_by_time(now_time - last_rec_time)

        x, y = mc.cal_character_pos_with_scale(self.lm_info, mm_info, possible_pos=(lx, ly, r))

        log.debug('截图计算坐标耗时 %.4f s', time.time() - start_time)

        return x, y, mm_info.angle

    def check_enemy_and_attack(self, mini_map: MatLike) -> bool:
        """
        从小地图检测敌人 如果有的话 进入索敌
        :param mini_map:
        :return: 是否有敌人
        """
        if not mini_map.is_under_attack(mini_map):
            return False
        # pos_list = mini_map.get_enemy_location(mini_map)
        # if len(pos_list) == 0:
        #     return False
        fight = EnterAutoFight(self.ctx)
        fight.execute()

        return True

import time

from basic.log_utils import log
from sr.config.game_config import get_game_config
from sr.context import Context
from sr.control import GameController
from sr.image.sceenshot import mini_map
from sr.map_cal import MapCalculator
from sr.operation import Operation


class EnterAutoFight(Operation):
    """
    根据小地图标点
    """

    def __init__(self, ctx: Context):
        self.ctx = ctx

    def execute(self) -> bool:
        attack_interval = 0.5  # 每0.5s发起一次攻击

        ctrl: GameController = self.ctx.controller
        mc: MapCalculator = self.ctx.map_cal
        ctrl.stop_moving_forward()
        last_attack_time = None
        while True:
            screen = ctrl.screenshot()

            now_time = time.time()
            screen_status = self.screen_status(screen)
            if screen_status != 'road':
                time.sleep(0.5)  # 战斗部分
                continue

            mm = mc.cut_mini_map(screen)
            # 根据小地图红点可能会搜索到障碍物后面的怪
            # pos_list = mini_map.get_enemy_location(mm)
            # if len(pos_list) == 0:
            #     log.info('附近已无怪')
            #     return True
            #
            # _, _, angle = mini_map.analyse_arrow_and_angle(mm, self.im)
            # ctrl.move_towards((mm.shape[0] // 2, mm.shape[1] // 2), pos_list[0], angle)

            if not mini_map.is_under_attack(mm, get_game_config().mini_map_pos):
                log.info('警报解除 索敌结束')
                return True

            if last_attack_time is None or now_time - last_attack_time > attack_interval:
                last_attack_time = now_time
                ctrl.initiate_attack()

    def screen_status(self, screen):
        return 'road'

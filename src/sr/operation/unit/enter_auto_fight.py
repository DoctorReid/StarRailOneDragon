import time

from basic.log_utils import log
from sr.config.game_config import get_game_config
from sr.context import Context
from sr.control import GameController
from sr.image.sceenshot import mini_map, battle
from sr.operation import Operation
from sr.operation.unit.enable_auto_fight import EnableAutoFight


class EnterAutoFight(Operation):
    """
    根据小地图标点
    """
    attack_interval = 1  # 发起攻击的间隔

    def __init__(self, ctx: Context):
        super().__init__(ctx)
        self.last_attack_time = time.time()
        self.ctx.controller.stop_moving_forward()
        log.info('检测到警报 索敌开始')

    def run(self) -> int:
        ctrl: GameController = self.ctx.controller

        screen = ctrl.screenshot()

        now_time = time.time()
        screen_status = battle.get_battle_status(screen, self.ctx.im)
        if screen_status != battle.IN_WORLD:
            eaf = EnableAutoFight(self.ctx)
            eaf.execute()
            time.sleep(0.5)  # 战斗部分
            return Operation.WAIT

        mm = mini_map.cut_mini_map(screen)
        # 根据小地图红点可能会搜索到障碍物后面的怪
        # pos_list = mini_map.get_enemy_location(mm)
        # if len(pos_list) == 0:
        #     log.info('附近已无怪')
        #     return True
        #
        # _, _, angle = mini_map.analyse_arrow_and_angle(mm, self.im)
        # ctrl.move_towards((mm.shape[0] // 2, mm.shape[1] // 2), pos_list[0], angle)

        if not mini_map.is_under_attack(mm, get_game_config().mini_map_pos):  # TODO 在线路末尾可能漏怪
            log.info('警报解除 索敌结束')
            return Operation.SUCCESS

        if now_time - self.last_attack_time > EnterAutoFight.attack_interval:
            self.last_attack_time = now_time
            ctrl.initiate_attack()
        return Operation.WAIT

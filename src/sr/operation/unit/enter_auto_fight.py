import time

from basic.i18_utils import gt
from basic.log_utils import log
from sr.config import game_config
from sr.context import Context
from sr.control import GameController
from sr.image.sceenshot import mini_map, battle
from sr.operation import Operation
from sr.operation.unit.enable_auto_fight import EnableAutoFight


class EnterAutoFight(Operation):
    """
    根据小地图的红圈
    """
    attack_interval = 0.5  # 发起攻击的间隔
    exit_after_no_alter_time = 2  # 多久没警报退出
    exit_after_no_battle_time = 20  # 持续多久没有进入战斗画面就退出 这时候大概率是小地图判断被怪物锁定有问题

    def __init__(self, ctx: Context):
        super().__init__(ctx, op_name=gt('进入战斗', 'ui'))
        self.last_attack_time = time.time()
        self.ctx.controller.stop_moving_forward()
        self.last_alert_time = time.time()  # 上次警报时间
        self.last_in_battle_time = time.time()  # 上次在战斗的时间
        self.with_battle: bool = False  # 是否有进入战斗
        log.info('索敌开始')

    def run(self) -> int:
        ctrl: GameController = self.ctx.controller

        screen = self.screenshot()

        now_time = time.time()
        screen_status = battle.get_battle_status(screen, self.ctx.im)
        if screen_status != battle.IN_WORLD:  # 在战斗界面
            eaf = EnableAutoFight(self.ctx)
            eaf.execute()
            time.sleep(0.5)  # 战斗部分
            self.last_in_battle_time = time.time()
            self.last_alert_time = self.last_in_battle_time
            self.with_battle = True
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

        if not mini_map.is_under_attack(mm, game_config.get().mini_map_pos, strict=True):
            if now_time - self.last_alert_time > EnterAutoFight.exit_after_no_alter_time:
                log.info('索敌结束')
                return Operation.SUCCESS if self.with_battle else Operation.FAIL
        else:
            self.last_alert_time = now_time

        if now_time - self.last_attack_time > EnterAutoFight.attack_interval:
            self.last_attack_time = now_time
            ctrl.initiate_attack()

        if now_time - self.last_in_battle_time > EnterAutoFight.exit_after_no_battle_time:
            return Operation.FAIL
        return Operation.WAIT

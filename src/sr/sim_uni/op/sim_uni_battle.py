import time
from typing import ClassVar, List, Optional

from cv2.typing import MatLike

from basic import Rect, str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr.context import Context
from sr.image.sceenshot import mini_map, screen_state
from sr.operation import Operation, OperationOneRoundResult, StateOperation, StateOperationNode, StateOperationEdge
from sr.operation.battle.start_fight import StartFightForElite
from sr.operation.unit.check_technique_point import CheckTechniquePoint
from sr.operation.unit.team import SwitchMember
from sr.screen_area.dialog import ScreenDialog
from sr.screen_area.screen_sim_uni import ScreenSimUni
from sr.sim_uni.op.sim_uni_choose_bless import SimUniChooseBless
from sr.sim_uni.op.sim_uni_choose_curio import SimUniChooseCurio
from sr.sim_uni.sim_uni_challenge_config import SimUniChallengeConfig


class SimUniEnterFight(Operation):

    ATTACK_INTERVAL: ClassVar[float] = 0.2  # 发起攻击的间隔
    EXIT_AFTER_NO_ALTER_TIME: ClassVar[int] = 2  # 多久没警报退出
    EXIT_AFTER_NO_BATTLE_TIME: ClassVar[int] = 20  # 持续多久没有进入战斗画面就退出 这时候大概率是小地图判断被怪物锁定有问题
    ATTACK_DIRECTION_ARR: ClassVar[List] = ['w', 's', 'a', 'd']

    STATUS_ENEMY_NOT_FOUND: ClassVar[str] = '未发现敌人'
    STATUS_BATTLE_FAIL: ClassVar[str] = '战斗失败'
    STATUS_STATE_UNKNOWN: ClassVar[str] = '未知状态'

    def __init__(self, ctx: Context,
                 config: Optional[SimUniChallengeConfig] = None,
                 disposable: bool = False,
                 no_attack: bool = False):
        """
        模拟宇宙中 主动进入战斗
        根据小地图的红圈 判断是否被敌人锁定
        """
        super().__init__(ctx, try_times=5,
                         op_name='%s %s' % (gt('模拟宇宙', 'ui'), gt('进入战斗', 'ui')))
        self.last_attack_time: float = 0
        self.last_alert_time: float = 0  # 上次警报时间
        self.last_not_in_world_time: float = 0  # 上次不在移动画面的时间
        self.last_state: str = ''  # 上一次的画面状态
        self.current_state: str = ''  # 这一次的画面状态
        self.with_battle: bool = False  # 是否有进入战斗
        self.attack_direction: int = 0  # 攻击方向
        self.config: Optional[SimUniChallengeConfig] = config  # 挑战配置
        self.disposable: bool = disposable  # 攻击可破坏物
        self.no_attack: bool = no_attack  # 不主动攻击
        self.use_technique: bool = False if config is None else config.technique_fight  # 是否使用秘技开怪

    def _init_before_execute(self):
        self.last_attack_time = time.time()
        self.last_alert_time = time.time()  # 上次警报时间
        self.last_not_in_world_time = time.time()  # 上次在战斗的时间

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        self.last_state = self.current_state
        self.current_state = self._get_screen_state(screen)

        log.debug('当前画面 %s', self.current_state)
        if self.current_state == screen_state.ScreenState.NORMAL_IN_WORLD.value:
            self._update_in_world()
            return self._try_attack(screen)
        elif self.current_state == screen_state.ScreenState.SIM_BLESS.value:
            return self._choose_bless()
        elif self.current_state == screen_state.ScreenState.SIM_CURIOS.value:
            return self._choose_curio()
        elif self.current_state == screen_state.ScreenState.EMPTY_TO_CLOSE.value:
            self.ctx.controller.click(screen_state.TargetRect.EMPTY_TO_CLOSE.value.center)
            return Operation.round_wait(wait=1)
        elif self.current_state == screen_state.ScreenState.BATTLE_FAIL.value:
            self.ctx.controller.click(screen_state.TargetRect.EMPTY_TO_CLOSE.value.center)
            return Operation.round_fail(SimUniEnterFight.STATUS_BATTLE_FAIL, wait=5)
        elif self.current_state == ScreenDialog.FAST_RECOVER_TITLE.value.text:
            result = self._recover_technique_point()
            self._update_not_in_world_time()  # 恢复秘技点的时间不应该在计算内
            return result
        elif self.current_state == screen_state.ScreenState.BATTLE.value:
            return self._in_battle()

        return Operation.round_retry(SimUniEnterFight.STATUS_STATE_UNKNOWN, wait=1)

    def _get_screen_state(self, screen: MatLike) -> Optional[str]:
        """
        获取当前屏幕状态
        :param screen: 屏幕截图
        :return:
        """
        return screen_state.get_sim_uni_screen_state(screen, self.ctx.im, self.ctx.ocr,
                                                     in_world=True,
                                                     battle=True,
                                                     battle_fail=True,
                                                     bless=True,
                                                     curio=True,
                                                     empty_to_close=True,
                                                     fast_recover=self.use_technique)

    def _update_in_world(self):
        """
        在大世界画面的更新
        :return:
        """
        if self.last_state != screen_state.ScreenState.NORMAL_IN_WORLD.value:
            self._update_not_in_world_time()

    def _update_not_in_world_time(self):
        """
        不在移动画面的情况
        更新一些统计时间
        :return:
        """
        now = time.time()
        self.last_not_in_world_time = now
        self.last_alert_time = now

    def _in_battle(self) -> Optional[OperationOneRoundResult]:
        """
        战斗
        :return:
        """
        self._update_not_in_world_time()
        self.with_battle = True
        self.ctx.technique_used = False
        return Operation.round_wait(wait=1)

    def _choose_bless(self) -> Optional[OperationOneRoundResult]:
        """
        选择祝福
        :return:
        """
        op = SimUniChooseBless(self.ctx, self.config)
        op_result = op.execute()
        self._update_not_in_world_time()

        if op_result.success:
            return Operation.round_wait(wait=1)
        else:
            return Operation.round_retry(op_result.status, wait=1)

    def _choose_curio(self) -> Optional[OperationOneRoundResult]:
        """
        选择奇物
        :return:
        """
        op = SimUniChooseCurio(self.ctx, self.config)
        op_result = op.execute()
        self._update_not_in_world_time()

        if op_result.success:
            return Operation.round_wait(wait=1)
        else:
            return Operation.round_retry(op_result.status, wait=1)

    def _try_attack(self, screen: MatLike) -> OperationOneRoundResult:
        """
        尝试主动攻击
        :param screen: 屏幕截图
        :return:
        """
        now_time = time.time()
        mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
        if not mini_map.is_under_attack(mm, self.ctx.game_config.mini_map_pos, strict=True):
            if now_time - self.last_alert_time > SimUniEnterFight.EXIT_AFTER_NO_ALTER_TIME:
                return Operation.round_success(None if self.with_battle else SimUniEnterFight.STATUS_ENEMY_NOT_FOUND)
        else:
            self.last_alert_time = now_time

        if now_time - self.last_not_in_world_time > SimUniEnterFight.EXIT_AFTER_NO_BATTLE_TIME:
            return Operation.round_success(None if self.with_battle else SimUniEnterFight.STATUS_ENEMY_NOT_FOUND)

        if self.no_attack:  # 适用于OP前就已经知道进入了战斗 这里只是等待战斗结束
            return Operation.round_success()
        elif self.disposable:
            self._attack(now_time)
        else:
            if self.use_technique and not self.ctx.is_buff_technique:  # 攻击类每次都需要使用
                self.ctx.technique_used = False

            if self.use_technique and not self.ctx.technique_used:
                technique_point = CheckTechniquePoint.get_technique_point(screen, self.ctx.ocr)

                if technique_point is None:  # 部分机器运行速度快 右上角图标出来了当下面秘技点还没出来 这时候还不能使用秘技
                    pass
                elif technique_point == 0 and self.ctx.no_technique_recover_consumables:  # 没有秘技恢复药了 就不使用了
                    pass
                elif self.ctx.is_buff_technique:
                    self.ctx.controller.use_technique()
                    self.ctx.technique_used = True  # 无论有没有秘技点 先设置已经使用了
                    self._update_not_in_world_time()  # 使用秘技的时间不应该在计算内
                elif mini_map.with_enemy_nearby(self.ctx.im, mm):  # 攻击类只有附近有敌人时候才使用
                    self.ctx.controller.use_technique()
                    self.ctx.technique_used = True  # 无论有没有秘技点 先设置已经使用了

                if self.ctx.technique_used and technique_point == 0:
                    self.last_alert_time += 0.5
                    return Operation.round_wait(wait=0.5)

            self._attack(now_time)

        return Operation.round_wait()

    def _recover_technique_point(self) -> OperationOneRoundResult:
        """
        恢复秘技点
        :return:
        """
        self.ctx.technique_used = False  # 重置使用情况

        screen = self.screenshot()
        if self.find_area(ScreenDialog.FAST_RECOVER_NO_CONSUMABLE.value, screen):
            self.ctx.no_technique_recover_consumables = True
            area = ScreenDialog.FAST_RECOVER_CANCEL.value
        else:
            if self.ctx.consumable_used and not self.config.multiple_consumable:  # 只使用一个消耗品
                area = ScreenDialog.FAST_RECOVER_CANCEL.value
            else:
                area = ScreenDialog.FAST_RECOVER_CONFIRM.value

        click = self.find_and_click_area(area, screen)

        if click == Operation.OCR_CLICK_SUCCESS:
            if area == ScreenDialog.FAST_RECOVER_CONFIRM.value:
                self.ctx.consumable_used = True
            else:
                self.ctx.consumable_used = False

            return Operation.round_wait(wait=0.5)
        else:
            return Operation.round_retry('点击%s失败' % area.text, wait=1)

    def _attack(self, now_time: float):
        if now_time - self.last_attack_time <= SimUniEnterFight.ATTACK_INTERVAL:
            return
        if self.disposable and self.attack_direction > 0:  # 可破坏物只攻击一次
            return
        self.last_attack_time = now_time
        if self.attack_direction > 0:
            self.ctx.controller.move(SimUniEnterFight.ATTACK_DIRECTION_ARR[self.attack_direction % 4])
            time.sleep(0.2)
        self.attack_direction += 1
        self.ctx.controller.initiate_attack()
        time.sleep(0.5)

    def on_resume(self):
        super().on_resume()
        self._update_not_in_world_time()


class SimUniFightElite(StateOperation):

    STATUS_ENEMY_NOT_FOUND: ClassVar[str] = '没有敌人'

    def __init__(self, ctx: Context, config: Optional[SimUniChallengeConfig] = None):
        """
        模拟宇宙 - 挑战精英、首领
        """
        edges = []

        check = StateOperationNode('检测敌人', self._check_enemy)
        technique_fight = StateOperationNode('秘技进入战斗', self._technique_fight)
        edges.append(StateOperationEdge(check, technique_fight, ignore_status=True))

        fight = StateOperationNode('战斗', self._fight)
        edges.append(StateOperationEdge(technique_fight, fight))

        switch = StateOperationNode('切换1号位', self._switch_1)
        edges.append(StateOperationEdge(fight, switch))
        edges.append(StateOperationEdge(check, switch, status=SimUniFightElite.STATUS_ENEMY_NOT_FOUND))

        super().__init__(ctx,
                         try_times=5,
                         op_name='%s %s' % (
                             gt('模拟宇宙', 'ui'),
                             gt('挑战精英首领', 'ui'),
                         ),
                         edges=edges
                         )
        self.config: Optional[SimUniChallengeConfig] = config  # 优先级

    def _check_enemy(self) -> OperationOneRoundResult:
        """
        判断当前是否有敌人
        :return:
        """
        area = ScreenSimUni.ENEMY_LEVEL.value
        screen = self.screenshot()

        if self.find_area(area, screen):
            return Operation.round_success()
        else:
            return Operation.round_success(SimUniFightElite.STATUS_ENEMY_NOT_FOUND)

    def _technique_fight(self) -> OperationOneRoundResult:
        op = StartFightForElite(self.ctx)
        return Operation.round_by_op(op.execute(), wait=1)

    def _fight(self) -> OperationOneRoundResult:
        area = ScreenSimUni.ENEMY_LEVEL.value
        screen = self.screenshot()
        if self.find_area(area, screen):  # 还没有进入战斗 可能是使用近战角色没有攻击到
            self.ctx.controller.initiate_attack()
            return Operation.round_retry('尝试攻击进入战斗画面')
        else:
            op = SimUniEnterFight(self.ctx, config=self.config, no_attack=True)  # 前面已经进行攻击了 这里不需要 且不额外使用秘技
            return Operation.round_by_op(op.execute())

    def _switch_1(self) -> OperationOneRoundResult:
        op = SwitchMember(self.ctx, 1)
        return Operation.round_by_op(op.execute())

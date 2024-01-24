import time
from typing import ClassVar, List, Optional

from cv2.typing import MatLike

from basic import Rect, str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.config import game_config
from sr.context import Context
from sr.image.sceenshot import mini_map, screen_state
from sr.operation import Operation, OperationOneRoundResult, StateOperation, StateOperationNode, StateOperationEdge
from sr.operation.battle.start_fight import StartFightWithTechnique
from sr.operation.unit.team import SwitchMember
from sr.sim_uni.op.sim_uni_choose_curio import SimUniChooseCurio
from sr.sim_uni.sim_uni_priority import SimUniBlessPriority, SimUniCurioPriority
from sr.sim_uni.op.sim_uni_choose_bless import SimUniChooseBless


class SimUniEnterFight(Operation):

    ATTACK_INTERVAL: ClassVar[float] = 0.2  # 发起攻击的间隔
    EXIT_AFTER_NO_ALTER_TIME: ClassVar[int] = 2  # 多久没警报退出
    EXIT_AFTER_NO_BATTLE_TIME: ClassVar[int] = 20  # 持续多久没有进入战斗画面就退出 这时候大概率是小地图判断被怪物锁定有问题
    ATTACK_DIRECTION_ARR: ClassVar[List] = ['w', 's', 'a', 'd']

    STATUS_ENEMY_NOT_FOUND: ClassVar[str] = '未发现敌人'
    STATUS_BATTLE_FAIL: ClassVar[str] = '战斗失败'
    STATUS_STATE_UNKNOWN: ClassVar[str] = '未知状态'

    def __init__(self, ctx: Context,
                 bless_priority: Optional[SimUniBlessPriority] = None,
                 curio_priority: Optional[SimUniBlessPriority] = None):
        """
        模拟宇宙中 主动进入战斗
        根据小地图的红圈 判断是否被敌人锁定
        """
        super().__init__(ctx, try_times=5,
                         op_name='%s %s' % (gt('模拟宇宙', 'ui'), gt('进入战斗', 'ui')))
        self.last_attack_time: float = 0
        self.last_alert_time: float = 0  # 上次警报时间
        self.last_not_in_world_time: float = 0  # 上次不在移动画面的时间
        self.with_battle: bool = False  # 是否有进入战斗
        self.attack_direction: int = 0  # 攻击方向
        self.bless_priority: Optional[SimUniBlessPriority] = bless_priority  # 祝福优先级
        self.curio_priority: Optional[SimUniBlessPriority] = curio_priority  # 奇物优先级

    def _init_before_execute(self):
        self.last_attack_time = time.time()
        self.last_alert_time = time.time()  # 上次警报时间
        self.last_not_in_world_time = time.time()  # 上次在战斗的时间

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        state = self._get_screen_state(screen)

        if state == screen_state.ScreenState.NORMAL_IN_WORLD.value:
            return self._try_attack(screen)
        elif state == screen_state.ScreenState.SIM_BLESS.value:
            return self._choose_bless()
        elif state == screen_state.ScreenState.SIM_CURIOS.value:
            return self._choose_curio()
        elif state == screen_state.ScreenState.BATTLE_FAIL.value:
            self.ctx.controller.click(screen_state.TargetRect.EMPTY_TO_CLOSE.value.center)
            return Operation.round_fail(SimUniEnterFight.STATUS_BATTLE_FAIL, wait=5)
        elif state == screen_state.ScreenState.BATTLE.value:
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
                                                     curio=True)

    def _update_not_in_world_time(self):
        """
        不在移动画面的情况
        更新一些统计时间
        :return:
        """
        self.last_not_in_world_time = time.time()
        self.last_alert_time = self.last_not_in_world_time
        self.with_battle = True

    def _in_battle(self) -> Optional[OperationOneRoundResult]:
        """
        战斗
        :return:
        """
        self._update_not_in_world_time()
        return Operation.round_wait(wait=1)

    def _choose_bless(self) -> Optional[OperationOneRoundResult]:
        """
        选择祝福
        :return:
        """
        op = SimUniChooseBless(self.ctx, self.bless_priority)
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
        op = SimUniChooseCurio(self.ctx, self.curio_priority)
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
        mm = mini_map.cut_mini_map(screen)
        if not mini_map.is_under_attack(mm, game_config.get().mini_map_pos, strict=True):
            if now_time - self.last_alert_time > SimUniEnterFight.EXIT_AFTER_NO_ALTER_TIME:
                return Operation.round_success(None if self.with_battle else SimUniEnterFight.STATUS_ENEMY_NOT_FOUND)
        else:
            self.last_alert_time = now_time

        if now_time - self.last_attack_time > SimUniEnterFight.ATTACK_INTERVAL:
            self.last_attack_time = now_time
            if self.attack_direction > 0:
                self.ctx.controller.move(SimUniEnterFight.ATTACK_DIRECTION_ARR[self.attack_direction % 4])
                time.sleep(0.2)
            self.attack_direction += 1
            self.ctx.controller.initiate_attack()
            time.sleep(0.5)

        if now_time - self.last_not_in_world_time > SimUniEnterFight.EXIT_AFTER_NO_BATTLE_TIME:
            return Operation.round_success(None if self.with_battle else SimUniEnterFight.STATUS_ENEMY_NOT_FOUND)

        return Operation.round_wait()

    def on_resume(self):
        super().on_resume()
        self._update_not_in_world_time()


class SimUniFightElite(StateOperation):

    ENEMY_LEVEL_RECT: ClassVar[Rect] = Rect(804, 38, 915, 75)  # 等级

    STATUS_ENEMY_NOT_FOUND: ClassVar[str] = '没有敌人'

    def __init__(self, ctx: Context,
                 bless_priority: Optional[SimUniBlessPriority] = None,
                 curio_priority: Optional[SimUniCurioPriority] = None):
        """
        模拟宇宙 - 挑战精英、首领
        """
        edges = []

        check = StateOperationNode('检测敌人', self._check_enemy)
        enter_fight = StateOperationNode('秘技进入战斗', self._enter_fight)
        edges.append(StateOperationEdge(check, enter_fight, ignore_status=True))

        fight = StateOperationNode('战斗', self._fight)
        edges.append(StateOperationEdge(enter_fight, fight))

        switch = StateOperationNode('切换1号位', self._switch_1)
        edges.append(StateOperationEdge(fight, switch))
        edges.append(StateOperationEdge(check, switch, status=SimUniFightElite.STATUS_ENEMY_NOT_FOUND))

        super().__init__(ctx,
                         op_name='%s %s' % (
                             gt('模拟宇宙', 'ui'),
                             gt('挑战精英首领', 'ui'),
                         ),
                         edges=edges
                         )
        self.bless_priority: Optional[SimUniBlessPriority] = bless_priority  # 祝福优先级
        self.curio_priority: Optional[SimUniBlessPriority] = curio_priority  # 奇物优先级

    def _check_enemy(self) -> OperationOneRoundResult:
        """
        判断当前是否有敌人
        :return:
        """
        screen = self.screenshot()
        part = cv2_utils.crop_image_only(screen, SimUniFightElite.ENEMY_LEVEL_RECT)
        osc_result = self.ctx.ocr.ocr_for_single_line(part)

        if str_utils.find_by_lcs(gt('等级', 'ocr'), osc_result, percent=0.1):
            return Operation.round_success()
        else:
            return Operation.round_success(SimUniFightElite.STATUS_ENEMY_NOT_FOUND)

    def _enter_fight(self) -> OperationOneRoundResult:
        op = StartFightWithTechnique(self.ctx)
        return Operation.round_by_op(op.execute())

    def _fight(self) -> OperationOneRoundResult:
        op = SimUniEnterFight(self.ctx, bless_priority=self.bless_priority, curio_priority=self.curio_priority)
        return Operation.round_by_op(op.execute())

    def _switch_1(self) -> OperationOneRoundResult:
        op = SwitchMember(self.ctx, 1)
        return Operation.round_by_op(op.execute())

import time
from typing import ClassVar, List, Optional

from cv2.typing import MatLike

from basic.i18_utils import gt
from sr.config import game_config
from sr.context import Context
from sr.image.sceenshot import mini_map, screen_state
from sr.operation import Operation, OperationOneRoundResult
from sr.sim_uni.op.sim_uni_choose_curio import SimUniChooseCurio
from sr.sim_uni.sim_uni_priority import SimUniBlessPriority
from sr.sim_uni.op.sim_uni_choose_bless import SimUniChooseBless


class SimUniEnterFight(Operation):

    ATTACK_INTERVAL: ClassVar[float] = 0.2  # 发起攻击的间隔
    EXIT_AFTER_NO_ALTER_TIME: ClassVar[int] = 2  # 多久没警报退出
    EXIT_AFTER_NO_BATTLE_TIME: ClassVar[int] = 20  # 持续多久没有进入战斗画面就退出 这时候大概率是小地图判断被怪物锁定有问题
    ATTACK_DIRECTION_ARR: ClassVar[List] = ['w', 's', 'a', 'd']

    STATUS_ENEMY_NOT_FOUND: ClassVar[str] = '未发现敌人'

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

        choose_bless = self._check_choose_bless(screen)
        if choose_bless is not None:
            return choose_bless

        choose_curio = self._check_choose_curio(screen)
        if choose_curio is not None:
            return choose_curio

        not_in_world = self._check_not_in_world(screen)
        if not_in_world is not None:
            return not_in_world

        return self._try_attack(screen)

    def _update_not_in_world_time(self):
        """
        不在移动画面的情况
        更新一些统计时间
        :return:
        """
        self.last_not_in_world_time = time.time()
        self.last_alert_time = self.last_not_in_world_time
        self.with_battle = True

    def _check_not_in_world(self, screen: MatLike) -> Optional[OperationOneRoundResult]:
        """
        检测是否不在大世界可移动页面
        - 战斗
        - 选择祝福
        :param screen: 屏幕截图
        :return:
        """
        if not screen_state.is_normal_in_world(screen, self.ctx.im):
            self._update_not_in_world_time()
            return Operation.round_wait(wait=1)
        else:
            return None

    def _check_choose_bless(self, screen: MatLike) -> Optional[OperationOneRoundResult]:
        """
        检查是否在选择祝福页面
        :param screen: 屏幕截图
        :return:
        """
        if not screen_state.in_sim_uni_choose_bless(screen, self.ctx.ocr):
            return None

        op = SimUniChooseBless(self.ctx, self.bless_priority)
        op_result = op.execute()
        self._update_not_in_world_time()

        if op_result.success:
            return Operation.round_wait(wait=1)
        else:
            return Operation.round_retry('选择祝福失败', wait=1)

    def _check_choose_curio(self, screen: MatLike) -> Optional[OperationOneRoundResult]:
        """
        检查是否在选择奇物页面
        :param screen: 屏幕截图
        :return:
        """
        if not screen_state.in_sim_uni_choose_curio(screen, self.ctx.ocr):
            return None

        op = SimUniChooseCurio(self.ctx, self.curio_priority)
        op_result = op.execute()
        self._update_not_in_world_time()

        if op_result.success:
            return Operation.round_wait(wait=1)
        else:
            return Operation.round_retry('选择奇物失败', wait=1)

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

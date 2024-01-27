import time
from typing import Optional, TypedDict, List, ClassVar

from cv2.typing import MatLike

from basic import str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr.app import AppRunRecord, AppDescription, register_app, Application2
from sr.config import ConfigHolder
from sr.context import Context
from sr.image.sceenshot import large_map
from sr.mystools import mys_config
from sr.operation import Operation, StateOperationNode, OperationOneRoundResult, StateOperationEdge
from sr.operation.combine.use_trailblaze_power import get_point_by_unique_id, TrailblazePowerPoint, UseTrailblazePower, \
    CATEGORY_5
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu
from sr.operation.unit.open_map import OpenMap

TRAILBLAZE_POWER = AppDescription(cn='开拓力', id='trailblaze_power')
register_app(TRAILBLAZE_POWER)


class TrailblazePowerRecord(AppRunRecord):

    def __init__(self):
        super().__init__(TRAILBLAZE_POWER.id)

    def _should_reset_by_dt(self):
        """
        根据米游社便签判断是否有足够体力进行下一次副本
        :return:
        """
        mys = mys_config.get()
        now = time.time()
        time_usage = now - mys.refresh_time
        power = mys.current_stamina + time_usage // 360  # 6分钟恢复一点体力
        config = get_config()
        if config.next_plan_item is not None:
            point: Optional[TrailblazePowerPoint] = get_point_by_unique_id(config.next_plan_item['point_id'])
            return point is not None and power >= point.power
        return False


trailblaze_power_record: Optional[TrailblazePowerRecord] = None


def get_record() -> TrailblazePowerRecord:
    global trailblaze_power_record
    if trailblaze_power_record is None:
        trailblaze_power_record = TrailblazePowerRecord()
    return trailblaze_power_record


class TrailblazePowerPlanItem(TypedDict):
    point_id: str  # 关卡id
    team_num: int  # 使用配队
    support: str
    plan_times: int  # 计划通关次数
    run_times: int  # 已经通关次数


class TrailblazePowerConfig(ConfigHolder):

    def __init__(self):
        super().__init__(TRAILBLAZE_POWER.id)

    def _init_after_read_file(self):
        """
        读取配置后的初始化
        :return:
        """
        # 兼容旧配置 对新增字段进行默认值的填充
        plan_list = self.plan_list
        any_changed: bool = False
        for plan_item in plan_list:
            if 'support' not in plan_item:
                plan_item['support'] = 'none'
                any_changed = True

        if any_changed:
            self.save()

    def check_plan_finished(self):
        """
        检测计划是否都执行完了
        执行完的话 所有执行次数置为0 重新开始下一轮
        :return:
        """
        plan_list: List[TrailblazePowerPlanItem] = self.plan_list
        for item in plan_list:
            if item['run_times'] < item['plan_times']:
                return

        # 全部都执行完了
        for item in plan_list:
            item['run_times'] = 0

        self.plan_list = plan_list

    @property
    def plan_list(self) -> List[TrailblazePowerPlanItem]:
        """
        体力规划配置
        :return:
        """
        return self.get('plan_list', [])

    @plan_list.setter
    def plan_list(self, new_list: List[TrailblazePowerPlanItem]):
        self.update('plan_list', new_list)

    @property
    def next_plan_item(self) -> Optional[TrailblazePowerPlanItem]:
        """
        按规划配置列表，找到第一个还没有完成的去执行
        如果都完成了 选择第一个
        :return: 下一个需要执行的计划
        """
        plan_list: List[TrailblazePowerPlanItem] = self.plan_list
        for item in plan_list:
            if item['run_times'] < item['plan_times']:
                return item

        if len(plan_list) > 0:
            return plan_list[0]

        return None


trailblaze_power_config: Optional[TrailblazePowerConfig] = None


def get_config() -> TrailblazePowerConfig:
    global trailblaze_power_config
    if trailblaze_power_config is None:
        trailblaze_power_config = TrailblazePowerConfig()
    return trailblaze_power_config


class TrailblazePower(Application2):

    STATUS_NORMAL_TASK: ClassVar[str] = '普通副本'
    STATUS_SIM_UNI_TASK: ClassVar[str] = '模拟宇宙'
    STATUS_NO_ENOUGH_POWER: ClassVar[str] = '体力不足'

    def __init__(self, ctx: Context):
        edges = []

        check_task = StateOperationNode('检查当前需要挑战的关卡', self._check_task)

        check_normal_power = StateOperationNode('检查剩余开拓力', self._check_power_for_normal)
        edges.append(StateOperationEdge(check_task, check_normal_power, status=TrailblazePower.STATUS_NORMAL_TASK))

        challenge_normal = StateOperationNode('挑战普通副本', self._challenge_normal_task)
        edges.append(StateOperationEdge(check_normal_power, challenge_normal))
        edges.append(StateOperationEdge(challenge_normal, check_task))  # 循环挑战

        esc = StateOperationNode('退出', self._esc)
        edges.append(StateOperationEdge(challenge_normal, esc, status=TrailblazePower.STATUS_NO_ENOUGH_POWER))

        check_sim_uni_power = StateOperationNode('检查剩余沉浸器', self._challenge_normal_task)
        challenge_sim_uni = StateOperationNode('挑战模拟宇宙', self._challenge_sim_uni)

        super().__init__(ctx, try_times=5,
                         op_name=gt('开拓力', 'ui'),
                         edges=edges, specified_start_node=check_task,
                         run_record=get_record())
        self.power: Optional[int] = None  # 剩余开拓力
        self.qty: Optional[int] = None  # 沉浸器数量
        self.last_challenge_point: Optional[TrailblazePowerPoint] = None
        self.config = get_config()

    def _init_before_execute(self):
        super()._init_before_execute()
        get_record().update_status(AppRunRecord.STATUS_RUNNING)
        self.last_challenge_point = None
        self.power = None

    def _check_task(self) -> OperationOneRoundResult:
        """
        判断下一个是什么副本
        :return:
        """
        self.config.check_plan_finished()
        plan: Optional[TrailblazePowerPlanItem] = self.config.next_plan_item

        if plan is None:
            return Operation.round_success()

        point: Optional[TrailblazePowerPoint] = get_point_by_unique_id(plan['point_id'])
        if point.category == CATEGORY_5:
            return Operation.round_success(TrailblazePower.STATUS_SIM_UNI_TASK)
        else:
            return Operation.round_success(TrailblazePower.STATUS_NORMAL_TASK)

    def _check_power_for_normal(self) -> OperationOneRoundResult:
        """
        普通副本 在大地图上看剩余体力
        :return:
        """
        if self.power is not None:  # 之前已经检测过了
            return Operation.round_success()

        op = OpenMap(self.ctx)
        op_result = op.execute()
        if not op_result.success:
            return Operation.round_retry('打开大地图失败')

        screen: MatLike = self.screenshot()
        part = cv2_utils.crop_image_only(screen, large_map.LARGE_MAP_POWER_RECT)
        ocr_result = self.ctx.ocr.ocr_for_single_line(part, strict_one_line=True)
        self.power = str_utils.get_positive_digits(ocr_result, err=None)
        if self.power is None:
            return Operation.round_retry('检测剩余开拓力失败', wait=1)
        else:
            log.info('识别当前开拓力 %d', self.power)
            return Operation.round_success()

    def _challenge_normal_task(self) -> OperationOneRoundResult:
        """
        挑战普通副本
        :return:
        """
        plan: Optional[TrailblazePowerPlanItem] = self.config.next_plan_item
        point: Optional[TrailblazePowerPoint] = get_point_by_unique_id(plan['point_id'])
        run_times: int = self.power // point.power
        if run_times == 0:
            return Operation.round_success(TrailblazePower.STATUS_NO_ENOUGH_POWER)
        if run_times + plan['run_times'] > plan['plan_times']:
            run_times = plan['plan_times'] - plan['run_times']

        op = UseTrailblazePower(self.ctx, point, plan['team_num'], run_times,
                                support=plan['support'] if plan['support'] != 'none' else None,
                                on_battle_success=self._on_normal_task_success,
                                need_transport=point != self.last_challenge_point)

        op_result = op.execute()
        if op_result.success:
            self.last_challenge_point = point
        return Operation.round_by_op(op_result)

    def _on_normal_task_success(self, finished_times: int, use_power: int):
        """
        普通副本获取一次奖励时候的回调
        :param finished_times: 完成次数
        :param use_power: 使用的体力
        :return:
        """
        log.info('挑战成功 完成次数 %d 使用体力 %d', finished_times, use_power)
        self.power -= use_power
        plan: Optional[TrailblazePowerPlanItem] = self.config.next_plan_item
        plan['run_times'] += finished_times
        self.config.save()

    def _esc(self) -> OperationOneRoundResult:
        op = OpenPhoneMenu(self.ctx)
        return Operation.round_by_op(op.execute())

    def _check_power_for_sim_uni(self) -> OperationOneRoundResult:
        pass

    def _challenge_sim_uni(self) -> OperationOneRoundResult:
        pass

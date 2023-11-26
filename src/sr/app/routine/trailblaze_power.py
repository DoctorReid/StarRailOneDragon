import time
from typing import Optional, TypedDict, List

from cv2.typing import MatLike

from basic import str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr.app import Application, AppRunRecord, AppDescription, register_app
from sr.config import ConfigHolder
from sr.context import Context
from sr.image.sceenshot import large_map
from sr.mystools import mys_config
from sr.operation import Operation
from sr.operation.combine.use_trailblaze_power import get_point_by_unique_id, TrailblazePowerPoint, UseTrailblazePower
from sr.operation.unit.open_map import OpenMap

TRAILBLAZE_POWER = AppDescription(cn='开拓力', id='trailblaze_power')
register_app(TRAILBLAZE_POWER)


class TrailblazePowerRecord(AppRunRecord):

    def __init__(self):
        super().__init__(TRAILBLAZE_POWER.id)

    def check_and_update_status(self):
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
            if point is not None and power >= point.power:
                self.update_status(AppRunRecord.STATUS_WAIT, only_status=True)


trailblaze_power_record: Optional[TrailblazePowerRecord] = None


def get_record() -> TrailblazePowerRecord:
    global trailblaze_power_record
    if trailblaze_power_record is None:
        trailblaze_power_record = TrailblazePowerRecord()
    return trailblaze_power_record


class TrailblazePowerPlanItem(TypedDict):
    point_id: str  # 关卡id
    team_num: int  # 使用配队
    plan_times: int  # 计划通关次数
    run_times: int  # 已经通关次数


class TrailblazePowerConfig(ConfigHolder):

    def __init__(self):
        super().__init__(TRAILBLAZE_POWER.id)

    def _init_after_read_file(self):
        pass

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


class TrailblazePower(Application):

    def __init__(self, ctx: Context):
        super().__init__(ctx, op_name=gt('开拓力', 'ui'))
        self.phase: int = 0
        self.power: int = 0
        self.last_challenge_point: Optional[TrailblazePowerPoint] = None

    def _init_before_execute(self):
        get_record().update_status(AppRunRecord.STATUS_RUNNING)
        self.last_challenge_point = None

    def _execute_one_round(self) -> int:
        if self.phase == 0:  # 打开大地图
            op = OpenMap(self.ctx)
            if not op.execute():
                return Operation.FAIL
            else:
                self.phase += 1
                return Operation.WAIT
        elif self.phase == 1:  # 查看剩余体力
            screen: MatLike = self.screenshot()
            part, _ = cv2_utils.crop_image(screen, large_map.LARGE_MAP_POWER_RECT)
            ocr_result = self.ctx.ocr.ocr_for_single_line(part, strict_one_line=True)
            self.power = str_utils.get_digits(ocr_result)
            log.info('当前体力 %d', self.power)
            self.phase += 1
            return Operation.WAIT
        elif self.phase == 2:  # 使用体力
            config = get_config()
            config.check_plan_finished()
            plan: Optional[TrailblazePowerPlanItem] = config.next_plan_item
            if plan is None:
                return Operation.SUCCESS

            record = get_record()

            point: Optional[TrailblazePowerPoint] = get_point_by_unique_id(plan['point_id'])
            run_times: int = self.power // point.power
            if run_times == 0:
                return Operation.SUCCESS
            if run_times + plan['run_times'] > plan['plan_times']:
                run_times = plan['plan_times'] - plan['run_times']

            def on_battle_success():
                self.power -= point.power
                log.info('消耗体力: %d, 剩余体力: %d', point.power, self.power)
                plan['run_times'] += 1
                log.info('副本完成次数: %d, 计划次数: %d', plan['run_times'], plan['plan_times'])
                config.save()
                record.update_status(AppRunRecord.STATUS_RUNNING)

            op = UseTrailblazePower(self.ctx, point, plan['team_num'], run_times, on_battle_success=on_battle_success,
                                    need_transport=point != self.last_challenge_point)
            if op.execute():
                self.last_challenge_point = point
                return Operation.WAIT
            else:
                return Operation.RETRY

    def _after_stop(self, result: bool):
        record = get_record()
        if result:
            record.update_status(AppRunRecord.STATUS_SUCCESS)
        else:
            record.update_status(AppRunRecord.STATUS_FAIL)

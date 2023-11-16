import re
from typing import Optional, TypedDict, List

from cv2.typing import MatLike

from basic import Rect
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr.app import Application, AppRunRecord, AppDescription, register_app
from sr.config import ConfigHolder
from sr.context import Context
from sr.operation import Operation
from sr.operation.combine.use_trailblaze_power import get_point_by_unique_id, TrailblazePowerPoint, UseTrailblazePower
from sr.operation.unit.open_map import OpenMap

TRAILBLAZE_POWER = AppDescription(cn='开拓力(测试中)', id='trailblaze_power')
register_app(TRAILBLAZE_POWER)


class TrailblazePowerRecord(AppRunRecord):

    def __init__(self):
        super().__init__(TRAILBLAZE_POWER.id)


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

    MAP_POWER_RECT = Rect(1635, 54, 1678, 72)

    def __init__(self, ctx: Context):
        super().__init__(ctx, op_name=gt('开拓力', 'ui'))
        self.phase: int = 0
        self.power: int = 0

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
            part, _ = cv2_utils.crop_image(screen, TrailblazePower.MAP_POWER_RECT)
            ocr_result = self.ctx.ocr.ocr_for_single_line(part, strict_one_line=True)
            digit_result = re.sub(r"\D", "", ocr_result)
            self.power = int(digit_result)
            log.info('当前体力 %d', self.power)
            self.phase += 1
            return Operation.WAIT
        elif self.phase == 2:  # 使用体力
            config = get_config()
            config.check_plan_finished()
            plan: Optional[TrailblazePowerPlanItem] = config.next_plan_item
            if plan is None:
                return Operation.SUCCESS

            point: Optional[TrailblazePowerPoint] = get_point_by_unique_id(plan['point_id'])
            run_times: int = self.power // point.power
            if run_times == 0:
                return Operation.SUCCESS
            if run_times + plan['run_times'] > plan['plan_times']:
                run_times = plan['plan_times'] - plan['run_times']

            def on_battle_success():
                self.power -= point.power
                plan['run_times'] += 1
                config.save()

            op = UseTrailblazePower(self.ctx, point, plan['team_num'], run_times, on_battle_success=on_battle_success)
            if op.execute():
                return Operation.WAIT
            else:
                return Operation.RETRY

from typing import Optional, TypedDict, List

from cv2.typing import MatLike

from basic import os_utils, str_utils
from basic.config import ConfigHolder
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr.app import AppDescription, register_app, AppRunRecord
from sr.app.application_base import Application
from sr.context import Context
from sr.image.sceenshot import large_map
from sr.operation import Operation
from sr.operation.combine.challenge_ehco_of_war import ChallengeEchoOfWar
from sr.interastral_peace_guide.survival_index_mission import SurvivalIndexCategoryEnum, SurvivalIndexMission, \
    SurvivalIndexMissionEnum
from sr.operation.unit.open_map import OpenMap

ECHO_OF_WAR = AppDescription(cn='历战余响', id='echo_of_war')
register_app(ECHO_OF_WAR)


class EchoOfWarPlanItem(TypedDict):
    point_id: str  # 关卡id - 旧 20240208 进行替换
    mission_id: str  # 关卡id - 新
    team_num: int  # 使用配队
    support: str  # 使用支援
    plan_times: int  # 计划通关次数
    run_times: int  # 已经通关次数


class EchoOfWarRecord(AppRunRecord):

    def __init__(self):
        super().__init__(ECHO_OF_WAR.id)

    def _should_reset_by_dt(self) -> bool:
        """
        根据时间判断是否应该重置状态 每周重置一次
        :return:
        """
        current_dt = self.get_current_dt()
        sunday_dt = os_utils.get_sunday_dt(self.dt)
        return current_dt > sunday_dt

    def reset_record(self):
        """
        运行记录重置 非公共部分由各app自行实现
        :return:
        """
        super().reset_record()
        self.left_times = 3

    @property
    def run_status_under_now(self):
        """
        基于当前时间显示的运行状态
        :return:
        """
        current_dt = self.get_current_dt()
        sunday_dt = os_utils.get_sunday_dt(self.dt)
        if current_dt > sunday_dt:
            return AppRunRecord.STATUS_WAIT
        else:
            return self.run_status

    @property
    def left_times(self) -> int:
        return self.get('left_times', 3)

    @left_times.setter
    def left_times(self, new_value: int):
        self.update('left_times', new_value)


echo_of_war_record: Optional[EchoOfWarRecord] = None


def get_record() -> EchoOfWarRecord:
    global echo_of_war_record
    if echo_of_war_record is None:
        echo_of_war_record = EchoOfWarRecord()
    return echo_of_war_record


class EchoOfWarConfig(ConfigHolder):

    def __init__(self):
        super().__init__(ECHO_OF_WAR.id)

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

            if 'mission_id' not in plan_item:
                plan_item['mission_id'] = plan_item['point_id']
                any_changed = True

        # 兼容旧配置 将新增的历战余响加入
        mission_list = SurvivalIndexMissionEnum.get_list_by_category(SurvivalIndexCategoryEnum.ECHO_OF_WAR.value)
        for i in mission_list:
            existed = False
            for plan_item in plan_list:
                if i.unique_id == plan_item['mission_id']:
                    existed = True
                    break
            if not existed:
                plan_list.append(EchoOfWarPlanItem(point_id=i.unique_id,
                                                   mission_id=i.unique_id,
                                                   team_num=1,
                                                   support='none',
                                                   plan_times=0,
                                                   run_times=0
                                                   ))
                any_changed = True

        if any_changed:
            self.save()

    def check_plan_finished(self):
        """
        检测计划是否都执行完了
        执行完的话 所有执行次数置为0 重新开始下一轮
        :return:
        """
        plan_list: List[EchoOfWarPlanItem] = self.plan_list
        for item in plan_list:
            if item['run_times'] < item['plan_times']:
                return

        # 全部都执行完了
        for item in plan_list:
            item['run_times'] = 0

    @property
    def plan_list(self) -> List[EchoOfWarPlanItem]:
        """
        体力规划配置
        :return:
        """
        return self.get('plan_list', [])

    @plan_list.setter
    def plan_list(self, new_list: List[EchoOfWarPlanItem]):
        self.update('plan_list', new_list)

    @property
    def next_plan_item(self) -> Optional[EchoOfWarPlanItem]:
        """
        按规划配置列表，找到第一个还没有完成的去执行
        如果都完成了 选择第一个
        :return: 下一个需要执行的计划
        """
        plan_list: List[EchoOfWarPlanItem] = self.plan_list
        for item in plan_list:
            if item['run_times'] < item['plan_times']:
                return item

        if len(plan_list) > 0:
            return plan_list[0]

        return None


echo_of_war_config: Optional[EchoOfWarConfig] = None


def get_config() -> EchoOfWarConfig:
    global echo_of_war_config
    if echo_of_war_config is None:
        echo_of_war_config = EchoOfWarConfig()

    return echo_of_war_config


class EchoOfWar(Application):

    def __init__(self, ctx: Context):
        super().__init__(ctx, op_name=gt('历战余响', 'ui'),
                         run_record=get_record())
        self.phase: int = 2
        self.power: int = 160

    def _init_before_execute(self):
        get_record().update_status(AppRunRecord.STATUS_RUNNING)

    def _execute_one_round(self) -> int:
        if self.phase == 0:  # 打开大地图
            op = OpenMap(self.ctx)
            if not op.execute().success:
                return Operation.FAIL
            else:
                self.phase += 1
                return Operation.WAIT
        elif self.phase == 1:  # 查看剩余体力
            screen: MatLike = self.screenshot()
            part, _ = cv2_utils.crop_image(screen, large_map.LARGE_MAP_POWER_RECT)
            ocr_result = self.ctx.ocr.ocr_for_single_line(part, strict_one_line=True)
            self.power = str_utils.get_positive_digits(ocr_result)
            log.info('当前体力 %d', self.power)
            self.phase += 1
            return Operation.WAIT
        elif self.phase == 2:  # 使用体力
            config = get_config()
            config.check_plan_finished()
            plan: Optional[EchoOfWarPlanItem] = config.next_plan_item
            if plan is None:
                return Operation.SUCCESS

            point: Optional[SurvivalIndexMission] = SurvivalIndexMissionEnum.get_by_unique_id(plan['mission_id'])

            run_times: int = self.power // point.power

            record = get_record()
            if record.left_times < run_times:
                run_times = record.left_times

            if run_times == 0:
                return Operation.SUCCESS

            if run_times + plan['run_times'] > plan['plan_times']:
                run_times = plan['plan_times'] - plan['run_times']

            def on_battle_success():
                self.power -= point.power
                log.info('消耗体力: %d, 剩余体力: %d', point.power, self.power)
                plan['run_times'] += 1
                log.info('副本完成次数: %d, 计划次数: %d', plan['run_times'], plan['plan_times'])
                record.left_times = record.left_times - 1
                log.info('本周历战余响剩余次数: %d', record.left_times)
                config.save()
                record.update_status(AppRunRecord.STATUS_RUNNING)

            op = ChallengeEchoOfWar(self.ctx, point.tp, plan['team_num'], run_times,
                                    support=plan['support'] if plan['support'] != 'none' else None,
                                    on_battle_success=on_battle_success)
            if op.execute().success:
                return Operation.WAIT
            else:  # 挑战
                return Operation.RETRY

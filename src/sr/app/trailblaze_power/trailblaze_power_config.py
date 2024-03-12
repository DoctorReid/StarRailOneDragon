from typing import TypedDict, Optional, List

from basic.config import ConfigHolder
from sr.app.app_description import AppDescriptionEnum


class TrailblazePowerPlanItem(TypedDict):
    point_id: str  # 关卡id - 旧 20240208 进行替换
    mission_id: str  # 关卡id - 新
    team_num: int  # 使用配队
    support: str
    plan_times: int  # 计划通关次数
    run_times: int  # 已经通关次数


class TrailblazePowerConfig(ConfigHolder):

    def __init__(self, account_idx: Optional[int] = None):
        super().__init__(AppDescriptionEnum.TRAILBLAZE_POWER.value.id, account_idx=account_idx)

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
        new_history_teams: List[TrailblazePowerPlanItem] = []
        new_mission_id_set: set[str] = set()
        for item in new_list:
            new_history_teams.append(item.copy())
            new_mission_id_set.add(item['mission_id'])

        old_history_teams = self.history_teams
        for item in old_history_teams:
            if item['mission_id'] not in new_mission_id_set:
                new_history_teams.append(item)

        self.update('history_teams', new_history_teams, False)
        self.update('plan_list', new_list)

    @property
    def history_teams(self) -> List[TrailblazePowerPlanItem]:
        """
        历史配置
        :return:
        """
        return self.get('history_teams', [])

    def get_history_by_id(self, mission_id: str) -> Optional[TrailblazePowerPlanItem]:
        old_history_teams = self.history_teams
        for item in old_history_teams:
            if item['mission_id'] == mission_id:
                return item
        return None

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

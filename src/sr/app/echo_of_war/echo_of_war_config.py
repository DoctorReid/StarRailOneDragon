from typing import TypedDict, List, Optional

from basic.config import ConfigHolder
from sr.app.app_description import AppDescriptionEnum
from sr.interastral_peace_guide.survival_index_mission import SurvivalIndexMissionEnum, SurvivalIndexCategoryEnum


class EchoOfWarPlanItem(TypedDict):
    point_id: str  # 关卡id - 旧 20240208 进行替换
    mission_id: str  # 关卡id - 新
    team_num: int  # 使用配队
    support: str  # 使用支援
    plan_times: int  # 计划通关次数
    run_times: int  # 已经通关次数


class EchoOfWarConfig(ConfigHolder):

    def __init__(self, account_idx: Optional[int] = None):
        super().__init__(AppDescriptionEnum.ECHO_OF_WAR.value.id, account_idx=account_idx)

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

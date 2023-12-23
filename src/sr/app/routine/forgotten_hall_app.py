import copy
import time
from typing import List, Optional, Set

from basic.i18_utils import gt
from basic.log_utils import log
from basic.os_utils import get_sunday_dt, dt_day_diff
from sr.app import AppRunRecord, AppDescription, register_app, app_record_current_dt_str, Application2
from sr.config import ConfigHolder
from sr.const import phone_menu_const
from sr.const.character_const import CharacterCombatType, get_character_by_id, Character, SILVERWOLF, ATTACK_PATH_LIST, \
    SURVIVAL_PATH_LIST, SUPPORT_PATH_LIST, is_attack_character, is_survival_character, is_support_character
from sr.context import Context
from sr.operation import OperationSuccess, OperationResult
from sr.operation.combine import StatusCombineOperationEdge2, \
    StatusCombineOperationNode
from sr.operation.combine.challenge_forgotten_hall_mission import ChallengeForgottenHallMission
from sr.operation.unit import guide
from sr.operation.unit.forgotten_hall.check_forgotten_hall_star import CheckForgottenHallStar
from sr.operation.unit.forgotten_hall.get_reward_in_fh import GetRewardInForgottenHall
from sr.operation.unit.guide import survival_index
from sr.operation.unit.guide.choose_guide_tab import ChooseGuideTab
from sr.operation.unit.guide.survival_index import ChooseSurvivalIndexCategory, ChooseSurvivalIndexMission
from sr.operation.unit.menu.click_phone_menu_item import ClickPhoneMenuItem
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu
from sr.performance_recorder import record_performance

FORGOTTEN_HALL = AppDescription(cn='忘却之庭', id='forgotten_hall')
register_app(FORGOTTEN_HALL)


class ForgottenHallRecord(AppRunRecord):

    def __init__(self):
        super().__init__(FORGOTTEN_HALL.id)

    def _should_reset_by_dt(self):
        """
        根据时间判断是否应该重置状态
        :return:
        """
        base_sunday = '20231126'

        old_sunday = get_sunday_dt(self.dt)
        old_sunday_day_diff = dt_day_diff(old_sunday, base_sunday)
        old_sunday_week_diff = old_sunday_day_diff // 7
        old_turn = old_sunday_week_diff // 2

        current_dt = app_record_current_dt_str()
        current_sunday = get_sunday_dt(current_dt)
        current_sunday_day_diff = dt_day_diff(current_sunday, base_sunday)
        current_sunday_week_diff = current_sunday_day_diff // 7
        current_turn = current_sunday_week_diff // 2

        return current_turn > old_turn

    def reset_record(self):
        """
        运行记录重置 非公共部分由各app自行实现
        :return:
        """
        super().reset_record()
        self.star = 0
        self.update('mission_stars', {})

    @property
    def star(self) -> int:
        return self.get('star', 0)

    @star.setter
    def star(self, new_value: int):
        self.update('star', new_value)

    @property
    def mission_stars(self) -> dict[int, int]:
        """
        各个关卡的星数
        :return:
        """
        return self.get('mission_stars', {})

    def get_mission_star(self, mission_num: int):
        """
        某个关卡的星数
        :param mission_num: 关卡编号
        :return: 星数
        """
        stars = self.mission_stars
        return stars[mission_num] if mission_num in stars else 0

    def update_mission_star(self, mission_num: int, star: int):
        """
        更新某个关卡的星数
        :param mission_num: 关卡编号
        :param star: 星数
        :return:
        """
        stars = self.mission_stars
        stars[mission_num] = star
        if 'mission_stars' not in self.data:
            self.update('mission_stars', stars, False)
        total_star: int = 0
        for v in stars.values():
            total_star += v
        if total_star > self.star:
            self.star = total_star
        self.save()


_forgotten_hall_record: Optional[ForgottenHallRecord] = None


def get_record() -> ForgottenHallRecord:
    global _forgotten_hall_record
    if _forgotten_hall_record is None:
        _forgotten_hall_record = ForgottenHallRecord()
    return _forgotten_hall_record


class ForgottenHallTeamModuleType:

    def __init__(self, module_type: str, module_name_cn: str):

        self.module_type: str = module_type
        """模块类型 唯一"""

        self.module_name_cn: str = module_name_cn
        """模块名称"""


TEAM_MODULE_ATTACK = ForgottenHallTeamModuleType(module_type='attack', module_name_cn='输出')
TEAM_MODULE_SURVIVAL = ForgottenHallTeamModuleType(module_type='survival', module_name_cn='生存')
TEAM_MODULE_SUPPORT = ForgottenHallTeamModuleType(module_type='support', module_name_cn='辅助')
TEAM_MODULE_LIST = [TEAM_MODULE_ATTACK, TEAM_MODULE_SURVIVAL, TEAM_MODULE_SUPPORT]

NODE_PHASE_ATTACK: int = 1  # 攻击
NODE_PHASE_CHANGE: int = 2  # 改变弱点
NODE_PHASE_SURVIVAL: int = 3  # 生存
NODE_PHASE_SUPPORT: int = 4  # 辅助


class ForgottenHallTeamModule:

    def __init__(self, module_name: str, combat_type: str, module_type: str, character_id_list: List[str]):

        self.module_name: str = module_name
        """配队名称"""

        self.combat_type: str = combat_type
        """应对属性 暂时不使用"""

        self.module_type: str = module_type
        """配队模块 暂时不使用"""

        self.character_id_list: List[str] = character_id_list
        """配队角色列表"""

    @property
    def with_attack(self) -> bool:
        """
        是否有输出位
        :return:
        """
        for character_id in self.character_id_list:
            if is_attack_character(character_id):
                return True
        return False

    @property
    def with_silver(self) -> bool:
        """
        是否有银狼
        :return:
        """
        return SILVERWOLF.id in self.character_id_list

    @property
    def with_survival(self) -> bool:
        """
        是否有生存位
        :return:
        """
        for character_id in self.character_id_list:
            if is_survival_character(character_id):
                return True
        return False

    @property
    def with_support(self) -> bool:
        """
        是否有辅助位
        :return:
        """
        for character_id in self.character_id_list:
            if is_support_character(character_id):
                return True
        return False

    @property
    def module_node_phase(self) -> int:
        """
        返回这个模块处于的配队节点状态
        :return:
        """
        with_attack = self.with_attack
        with_silver = self.with_silver
        with_survival = self.with_survival
        next_node_phase = NODE_PHASE_ATTACK
        if not with_attack:
            next_node_phase = NODE_PHASE_CHANGE
        if not with_attack and not with_silver:
            next_node_phase = NODE_PHASE_SURVIVAL
        if not with_attack and not with_silver and not with_survival:
            next_node_phase = NODE_PHASE_SUPPORT
        return next_node_phase


class ForgottenHallNodeTeam:

    def __init__(self):

        self.module_list: List[ForgottenHallTeamModule] = []
        """使用的配队模块"""

        self.character_id_set: Set[str] = set()
        """角色ID集合"""

        self.node_dfs_phase: int = 0
        """搜索状态 模块需要按影响得分顺序添加 输出 -> 银狼 -> 生存 -> 辅助"""

    @property
    def character_list(self) -> List[Character]:
        """
        :return: 角色列表
        """
        character_list: List[Character] = []
        for character_id in self.character_id_set:
            character_list.append(get_character_by_id(character_id))
        return character_list

    def existed_characters(self, character_id_list: List[str]) -> bool:
        """
        判断角色列表是否已经在列表中存在了
        :param character_id_list:
        :return:
        """
        for character_id in character_id_list:
            if character_id in self.character_id_set:
                return True
        return False

    @property
    def with_attack(self) -> bool:
        """
        是否有输出位
        :return:
        """
        for module in self.module_list:
            for character_id in module.character_id_list:
                if is_attack_character(character_id):
                    return True
        return False

    @property
    def with_silver(self) -> bool:
        """
        是否有银狼
        :return:
        """
        for character_id in self.character_id_set:
            if character_id == SILVERWOLF.id:
                return True
        return False

    @property
    def with_survival(self) -> bool:
        """
        是否有生存位
        :return:
        """
        for module in self.module_list:
            for character_id in module.character_id_list:
                if is_survival_character(character_id):
                    return True
        return False

    @property
    def with_support(self) -> bool:
        """
        是否有辅助位
        :return:
        """
        for module in self.module_list:
            for character_id in module.character_id_list:
                if is_support_character(character_id):
                    return True
        return False

    @property
    def character_cnt(self) -> int:
        """
        角色数量
        :return:
        """
        return len(self.character_id_set)

    def add_module(self, module: ForgottenHallTeamModule):
        """
        添加配队模块
        :param module: 配队模块
        :return:
        """
        self.module_list.append(module)
        for character_id in module.character_id_list:
            self.character_id_set.add(character_id)

    def pop_module(self, module: ForgottenHallTeamModule) -> bool:
        """
        删除配队模块
        :param module: 配队模块
        :return: 是否删除成功
        """
        try:
            self.module_list.remove(module)
            for character_id in module.character_id_list:
                self.character_id_set.remove(character_id)
            return True
        except Exception:
            log.error('弹出配队模块失败', exc_info=True)
            return False


class ForgottenHallNodeTeamScore:

    def __init__(self, node_team: ForgottenHallNodeTeam, combat_type_list: List[CharacterCombatType]):
        """
        节点配队得分模型
        :param node_team: 节点配队
        :param combat_type_list: 节点需要的属性
        """

        self.attack_cnt: int = 0
        """输出数量"""

        self.support_cnt: int = 0
        """支援数量"""

        self.survival_cnt: int = 0
        """生存数量"""

        self.combat_type_not_need_cnt: int = 0
        """配队中原本多余的属性个数"""

        self.combat_type_attack_cnt: int = 0
        """输出位对应属性的数量"""

        self.combat_type_attack_cnt_under_silver: int = 0
        """输出位在拥有银狼情况下对应属性的数量"""

        self.combat_type_other_cnt: int = 0
        """其他位对应属性的数量"""

        self.combat_type_other_cnt_under_silver: int = 0
        """其它位在拥有银狼情况下对应属性的数量"""

        self.cnt_score: float = 0
        """人数得分"""

        self.attack_score: float = 0
        """输出位得分"""

        self.survival_score: float = 0
        """生存位得分"""

        self.support_score: float = 0
        """辅助位得分"""

        self.combat_type_score: float = 0
        """对应属性得分"""

        self.total_score: float = 0
        """总得分"""

        character_list = node_team.character_list
        cal_combat_type_list = self._cal_need_combat_type(character_list, combat_type_list)

        self._cal_character_cnt(character_list, combat_type_list, cal_combat_type_list)
        self._cal_total_score()

    def _cal_need_combat_type(self,
                              character_list: List[Character],
                              need_combat_type_list: List[CharacterCombatType]):
        """
        计算在配队中真正需要的属性列表
        :param character_list: 当前角色列表
        :param need_combat_type_list: 原来需要的属性列表
        :return: 由配队调整后的属性列表
        """
        if SILVERWOLF in character_list:  # 有银狼的情况 可以添加弱点
            team_combat_type_not_in_need: Set[CharacterCombatType] = set()
            for c in character_list:
                if c.combat_type not in need_combat_type_list:
                    team_combat_type_not_in_need.add(c.combat_type)
            self.combat_type_not_need_cnt = len(team_combat_type_not_in_need)
            cal: List[CharacterCombatType] = []
            for ct in need_combat_type_list:
                cal.append(ct)
            for ct in team_combat_type_not_in_need:
                cal.append(ct)
            return cal
        else:
            return need_combat_type_list

    def _cal_character_cnt(self,
                           character_list: List[Character],
                           origin_combat_type_list: List[CharacterCombatType],
                           cal_combat_type_list: List[CharacterCombatType]):
        """
        统计各种角色的数量
        :param character_list: 角色列表
        :param cal_combat_type_list: 节点需要的属性
        :return:
        """
        for c in character_list:
            if c.path in ATTACK_PATH_LIST:
                self.attack_cnt += 1
                if c.combat_type in origin_combat_type_list:
                    self.combat_type_attack_cnt += 1
                elif c.combat_type in cal_combat_type_list:
                    self.combat_type_attack_cnt_under_silver += 1
            elif c.path in SURVIVAL_PATH_LIST:
                self.survival_cnt += 1
                if c.combat_type in origin_combat_type_list:
                    self.combat_type_other_cnt += 1
                elif c.combat_type in cal_combat_type_list:
                    self.combat_type_other_cnt_under_silver += 1
            elif c.path in SUPPORT_PATH_LIST:
                self.support_cnt += 1
                if c.combat_type in origin_combat_type_list:
                    self.combat_type_other_cnt += 1
                elif c.combat_type in cal_combat_type_list:
                    self.combat_type_other_cnt_under_silver += 1

    def _cal_total_score(self):
        """
        计算总分
        :return:
        """
        # 人数尽量多
        cnt_base = 1e8
        self.cnt_score = (self.attack_cnt + self.survival_cnt + self.support_cnt) * cnt_base

        # 要有输出位
        # 输出并不是越多越好 有符合属性的输出才是最重要的 同时至少要有一个输出位
        # 输出分 = 输出位基数 + 输出位属性分
        # 输出位属性分 =
        #   1. 有原属性符合的输出 -> 符合属性基数
        #   2. 无原属性符合的输出 但有银狼 -> 0.9 * 符合属性基数 / 配队中多余的属性个数
        attack_combat_type_base = 1e7  # 符合属性基数
        attack_normal_base = 1e6  # 输出位基数
        self.attack_score = 0
        if self.attack_cnt > 0:
            self.attack_score += attack_normal_base
        if self.combat_type_attack_cnt > 0:
            self.attack_score += attack_combat_type_base
        elif self.combat_type_attack_cnt_under_silver > 0 and self.combat_type_not_need_cnt > 0:  # 比例 转化 银狼转化的输出分要打一定折扣 优先选原属性就符合的
            self.attack_score += 0.9 * attack_combat_type_base / self.combat_type_not_need_cnt

        # 其次必须要有生存位 但不宜超过一个
        # 生存分 = 生存位基础基数
        survival_base = 1e5
        if self.survival_cnt > 0:
            self.survival_score += survival_base

        # 辅助位越多越好
        # 辅助分 = 辅助数量 * 辅助分基数
        support_base = 1e4
        self.support_score = self.support_cnt * support_base

        # 最后看符合属性的数量
        # 属性分 = 原属性符合的数量 * 属性基数 + 0.9 * 银狼加持下属性符合的数量 * 属性基数 / 配队中多余的属性个数
        combat_type_base = 1e3
        self.combat_type_score = (self.combat_type_attack_cnt + self.combat_type_other_cnt) * combat_type_base
        if self.combat_type_not_need_cnt > 0:
            self.combat_type_score += 0.9 * (self.combat_type_attack_cnt_under_silver + self.combat_type_other_cnt_under_silver) * combat_type_base / self.combat_type_not_need_cnt

        self.total_score = self.cnt_score + self.attack_score + self.survival_score + self.support_score + self.combat_type_score


class ForgottenHallMissionTeam:

    def __init__(self, node_combat_types: List[List[CharacterCombatType]]):
        total_node_cnt: int = len(node_combat_types)
        node_team_list = []
        for _ in range(total_node_cnt):
            node_team_list.append(ForgottenHallNodeTeam())

        self.total_node_cnt: int = total_node_cnt
        """总节点数"""

        self.node_combat_types: List[List[CharacterCombatType]] = node_combat_types
        """节点对应属性"""

        self.node_team_list: List[ForgottenHallNodeTeam] = node_team_list
        """节点队伍列表"""

        self.cnt_score: float = 0
        """人数得分"""

        self.attack_score: float = 0
        """输出位得分"""

        self.survival_score: float = 0
        """生存位得分"""

        self.support_score: float = 0
        """辅助位得分"""

        self.combat_type_score: float = 0
        """对应属性得分"""

        self.total_score: float = 0
        """总得分"""

    def existed_characters(self, character_id_list: List[str]) -> bool:
        """
        判断角色列表是否已经在列表中存在了
        :param character_id_list:
        :return:
        """
        for node_team in self.node_team_list:
            if node_team.existed_characters(character_id_list):
                return True
        return False

    def add_to_node(self, node_num: int, module: ForgottenHallTeamModule) -> bool:
        """
        添加角色到对应节点配队中
        :param node_num: 节点编号
        :param module: 配队模块
        :return: 是否成功添加
        """
        if len(self.node_team_list[node_num].character_id_set) + len(module.character_id_list) > 4:  # 超过人数限制
            return False
        if self.existed_characters(module.character_id_list):
            return False
        else:
            self.node_team_list[node_num].add_module(module)
            return True

    def pop_from_node(self, node_num: int, module: ForgottenHallTeamModule) -> bool:
        """
        从对应节点中删除模块
        :param node_num: 节点编号
        :param module: 配队模块
        :return: 是否删除成功
        """
        if node_num >= len(self.node_team_list):
            return False
        return self.node_team_list[node_num].pop_module(module)

    @property
    def valid_mission_team(self) -> bool:
        """
        关卡配队是否合法
        所有节点都有至少一个角色就算合法
        :return: 是否合法
        """
        for node_team in self.node_team_list:
            if node_team.character_cnt == 0:
                return False

        return True

    @property
    def character_list(self) -> List[List[Character]]:
        ret_list = []
        for node_team in self.node_team_list:
            ret_list.append(node_team.character_list)
        return ret_list

    @property
    def character_cnt(self) -> int:
        """
        角色数量
        :return:
        """
        total_cnt = 0
        for node_team in self.node_team_list:
            total_cnt += node_team.character_cnt
        return total_cnt

    def update_score(self):
        """
        更新得分
        :return:
        """
        self.cnt_score = 0
        self.attack_score = 0
        self.survival_score = 0
        self.support_score = 0
        self.combat_type_score = 0
        self.total_score = 0

        if not self.valid_mission_team:  # 不合法的配队 没有得分
            return

        for i in range(len(self.node_combat_types)):
            node = ForgottenHallNodeTeamScore(self.node_team_list[i], self.node_combat_types[i])
            self.cnt_score += node.cnt_score
            self.attack_score += node.attack_score
            self.survival_score += node.survival_score
            self.support_score += node.support_score
            self.combat_type_score += node.combat_type_score
            self.total_score += node.total_score


class ForgottenHallConfig(ConfigHolder):

    def __init__(self):
        ConfigHolder.__init__(self, FORGOTTEN_HALL.id)

    def _init_after_read_file(self):
        pass

    @property
    def team_module_list(self) -> List[ForgottenHallTeamModule]:
        arr = self.get('team_module_list', [])
        ret = []
        for i in arr:
            ret.append(ForgottenHallTeamModule(**i))
        return ret

    @team_module_list.setter
    def team_module_list(self, new_list: List[ForgottenHallTeamModule]):
        dict_arr = []
        for i in new_list:
            dict_arr.append(vars(i))
        self.update('team_module_list', dict_arr)


_forgotten_hall_config: Optional[ForgottenHallConfig] = None


def get_config() -> ForgottenHallConfig:
    global _forgotten_hall_config
    if _forgotten_hall_config is None:
        _forgotten_hall_config = ForgottenHallConfig()
    return _forgotten_hall_config


class ForgottenHallApp(Application2):

    def __init__(self, ctx: Context):
        self.run_record: Optional[ForgottenHallRecord] = get_record()
        edges: List[StatusCombineOperationEdge2] = []

        open_menu = StatusCombineOperationNode('打开菜单', OpenPhoneMenu(ctx))
        choose_guide = StatusCombineOperationNode('选择【指南】', ClickPhoneMenuItem(ctx, phone_menu_const.INTERASTRAL_GUIDE))
        edges.append(StatusCombineOperationEdge2(open_menu, choose_guide))

        choose_survival = StatusCombineOperationNode('选择【生存索引】', ChooseGuideTab(ctx, guide.GUIDE_TAB_3))
        edges.append(StatusCombineOperationEdge2(choose_guide, choose_survival))

        choose_fh = StatusCombineOperationNode('选择【忘却之庭】', ChooseSurvivalIndexCategory(ctx, survival_index.CATEGORY_FORGOTTEN_HALL))
        edges.append(StatusCombineOperationEdge2(choose_survival, choose_fh))

        fh_tp = StatusCombineOperationNode('传送', ChooseSurvivalIndexMission(ctx, survival_index.MISSION_FORGOTTEN_HALL))
        edges.append(StatusCombineOperationEdge2(choose_fh, fh_tp))

        get_reward = StatusCombineOperationNode('领取奖励', GetRewardInForgottenHall(ctx))

        check_total_star = StatusCombineOperationNode('检测总星数', CheckForgottenHallStar(ctx, self._update_star))
        edges.append(StatusCombineOperationEdge2(fh_tp, check_total_star))  # 满星的时候直接设置为成功
        edges.append(StatusCombineOperationEdge2(check_total_star, get_reward, status='30'))  # 满星的时候直接设置为成功

        last_mission = StatusCombineOperationNode('模拟上个关卡满星', OperationSuccess(ctx, '3'))
        edges.append(StatusCombineOperationEdge2(check_total_star, last_mission, ignore_status=True))  # 非满星的时候开始挑战

        for i in range(10):  # 循环挑战10个关卡
            if self.run_record.get_mission_star(i + 1) == 3:  # 已经满星就跳过
                continue
            mission = StatusCombineOperationNode(
                '挑战关卡 %d' % (i + 1),
                ChallengeForgottenHallMission(ctx, i + 1, 2,
                                              cal_team_func=self._cal_team_member,
                                              mission_star_callback=self._update_mission_star))
            edges.append(StatusCombineOperationEdge2(last_mission, mission, status='3'))  # 只有上一次关卡满星再进入下一个关卡

            edges.append(StatusCombineOperationEdge2(mission, get_reward, ignore_status=True))  # 没满星就不挑战下一个了

            last_mission = mission

        edges.append(StatusCombineOperationEdge2(last_mission, get_reward, ignore_status=True))  # 最后一关无论结果如何都结束 尝试领取奖励

        super().__init__(ctx, op_name=gt('忘却之庭', 'ui'),
                         run_record=self.run_record, edges=edges)
        self.config: ForgottenHallConfig = get_config()

    def _update_star(self, star: int):
        log.info('忘却之庭 当前总星数 %d', star)
        self.run_record.star = star

    def _update_mission_star(self, mission_num: int, star: int):
        log.info('忘却之庭 关卡 %d 当前星数 %d', mission_num, star)
        self.run_record.update_mission_star(mission_num, star)

    def _cal_team_member(self, node_combat_types: List[List[CharacterCombatType]]) -> Optional[List[List[Character]]]:
        """
        根据关卡属性计算对应配队
        :param node_combat_types: 节点对应的属性
        :return:
        """
        module_list = self.config.team_module_list
        log.info('开始计算配队 所需属性为 %s', [i.cn for combat_types in node_combat_types for i in combat_types])
        return self.search_best_mission_team(node_combat_types, module_list)

    @staticmethod
    @record_performance
    def search_best_mission_team(
            node_combat_types: List[List[CharacterCombatType]],
            config_module_list: List[ForgottenHallTeamModule]) -> Optional[List[List[Character]]]:
        """
        穷举配队组合
        :param node_combat_types: 节点对应属性
        :param config_module_list: 配队模块列表
        :return: 配队组合
        """
        total_node_cnt: int = len(node_combat_types)
        best_mission_team: Optional[ForgottenHallMissionTeam] = None

        # 先排序 保证可以按阶段搜索
        sorted_config_module_list = sorted(config_module_list, key=lambda x: x.module_node_phase)

        def impossibly_greater(current_mission_team: ForgottenHallMissionTeam) -> bool:
            """
            当前配队是否不可能比之前最好的记录更好了
            :param current_mission_team: 当前配队
            :return:
            """
            if not current_mission_team.valid_mission_team:  # 未完成配队
                return False

            if best_mission_team is None:  # 暂时没有最佳配队
                return False

            current_mission_team.update_score()
            all_node_after_attack_and_silver: bool = True  # 所有节点都选过输出和银狼了
            all_node_after_survival: bool = True  # 所有节点都选过生存位了
            for i in range(total_node_cnt):
                node_team = current_mission_team.node_team_list[i]
                if node_team.node_dfs_phase <= 1:
                    all_node_after_attack_and_silver = False
                if node_team.node_dfs_phase <= 2:
                    all_node_after_survival = False

            if all_node_after_attack_and_silver and current_mission_team.attack_score < best_mission_team.attack_score:
                # 选完输出位和银狼 攻击分还落后 就不可能更好
                return True
            elif all_node_after_survival:
                if current_mission_team.survival_score < best_mission_team.survival_score:
                    # 选完生存位 生存分还落后 就不可能更好 生存分只有一种
                    return True
                elif current_mission_team.support_score + (8 - current_mission_team.character_cnt) * 1e4 < best_mission_team.support_score:
                    # 选完生存位 生存分一样 辅助分不可能跟上
                    return True
                elif current_mission_team.support_score + (8 - current_mission_team.character_cnt) * 1e4 == best_mission_team.support_score:
                    # 选完生存位 生存分一样 辅助分有可能一样
                    if current_mission_team.combat_type_score + (8 - current_mission_team.character_cnt) * 1e3 < best_mission_team.combat_type_score:
                        # 选完生存位 生存分一样 辅助分有可能一样 但属性分不可能跟上
                        return True

            return False

        def dfs(current_mission_team: ForgottenHallMissionTeam,
                current_module_idx: int):
            """
            递归遍历配队组合 这里只会先按节点数量选出队伍 后续再由评分模型判断哪个队伍去哪个节点
            :param current_mission_team: 当前的配队
            :param current_module_idx: 当前使用的模块下标
            :return:
            """
            if current_module_idx == len(sorted_config_module_list):
                if current_mission_team.valid_mission_team:
                    current_mission_team.update_score()
                    nonlocal best_mission_team
                    if best_mission_team is None or current_mission_team.total_score > best_mission_team.total_score:
                        best_mission_team = copy.deepcopy(current_mission_team)
                return

            if impossibly_greater(current_mission_team):
                return

            module = sorted_config_module_list[current_module_idx]
            next_node_phase = module.module_node_phase

            for node_idx in range(total_node_cnt):  # 使用当前模块加入
                node_team = current_mission_team.node_team_list[node_idx]
                if next_node_phase >= node_team.node_dfs_phase:  # 可以加入当前节点
                    if current_mission_team.add_to_node(node_idx, module):  # 添加模块到当前节点
                        temp_phase = node_team.node_dfs_phase
                        node_team.node_dfs_phase = next_node_phase

                        dfs(current_mission_team, current_module_idx + 1)

                        current_mission_team.pop_from_node(node_idx, module)  # 弹出模块
                        node_team.node_dfs_phase = temp_phase

            # 不使用当前模块加入
            dfs(current_mission_team, current_module_idx + 1)

        start_time = time.time()
        dfs(ForgottenHallMissionTeam(node_combat_types), 0)  # 搜索
        log.info('组合配队完成 耗时 %.2f秒', time.time() - start_time)

        if best_mission_team is None:
            return None
        else:
            return best_mission_team.character_list

    def _update_record_stop(self, result: OperationResult):
        """
        应用停止后的对运行记录的更新
        :param result: 运行结果
        :return:
        """
        if not result.success or self.run_record.star < 30:
            self.run_record.update_status(AppRunRecord.STATUS_FAIL)
        else:
            self.run_record.update_status(AppRunRecord.STATUS_SUCCESS)

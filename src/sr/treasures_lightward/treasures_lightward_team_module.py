import time
from typing import List, Set, Optional

from basic.log_utils import log
from sr.const.character_const import is_attack_character, SILVERWOLF, is_survival_character, is_support_character, \
    Character, get_character_by_id, CharacterCombatType, ATTACK_PATH_LIST, SURVIVAL_PATH_LIST, SUPPORT_PATH_LIST
from sr.performance_recorder import record_performance


class TreasuresLightwardTeamModuleType:

    def __init__(self, module_type: str, module_name_cn: str):

        self.module_type: str = module_type
        """模块类型 唯一"""

        self.module_name_cn: str = module_name_cn
        """模块名称"""


TEAM_MODULE_ATTACK = TreasuresLightwardTeamModuleType(module_type='attack', module_name_cn='输出')
TEAM_MODULE_SURVIVAL = TreasuresLightwardTeamModuleType(module_type='survival', module_name_cn='生存')
TEAM_MODULE_SUPPORT = TreasuresLightwardTeamModuleType(module_type='support', module_name_cn='辅助')
TEAM_MODULE_LIST = [TEAM_MODULE_ATTACK, TEAM_MODULE_SURVIVAL, TEAM_MODULE_SUPPORT]
NODE_PHASE_ATTACK: int = 1  # 攻击
NODE_PHASE_CHANGE: int = 2  # 改变弱点
NODE_PHASE_SURVIVAL: int = 3  # 生存
NODE_PHASE_SUPPORT: int = 4  # 辅助


class TreasuresLightwardTeamModule:

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


class TreasuresLightwardNodeTeam:

    def __init__(self):

        self.module_list: List[TreasuresLightwardTeamModule] = []
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

    def add_module(self, module: TreasuresLightwardTeamModule):
        """
        添加配队模块
        :param module: 配队模块
        :return:
        """
        self.module_list.append(module)
        for character_id in module.character_id_list:
            self.character_id_set.add(character_id)

    def pop_module(self, module: TreasuresLightwardTeamModule) -> bool:
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


class TreasuresLightwardNodeTeamScore:

    def __init__(self, node_team: TreasuresLightwardNodeTeam, combat_type_list: List[CharacterCombatType]):
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


class TreasuresLightwardMissionTeam:

    def __init__(self, node_combat_types: List[List[CharacterCombatType]]):
        total_node_cnt: int = len(node_combat_types)
        node_team_list = []
        for _ in range(total_node_cnt):
            node_team_list.append(TreasuresLightwardNodeTeam())

        self.total_node_cnt: int = total_node_cnt
        """总节点数"""

        self.node_combat_types: List[List[CharacterCombatType]] = node_combat_types
        """节点对应属性"""

        self.node_team_list: List[TreasuresLightwardNodeTeam] = node_team_list
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

    def add_to_node(self, node_num: int, module: TreasuresLightwardTeamModule) -> bool:
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

    def pop_from_node(self, node_num: int, module: TreasuresLightwardTeamModule) -> bool:
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
            node = TreasuresLightwardNodeTeamScore(self.node_team_list[i], self.node_combat_types[i])
            self.cnt_score += node.cnt_score
            self.attack_score += node.attack_score
            self.survival_score += node.survival_score
            self.support_score += node.support_score
            self.combat_type_score += node.combat_type_score
            self.total_score += node.total_score



@record_performance
def search_best_mission_team(
        node_combat_types: List[List[CharacterCombatType]],
        config_module_list: List[TreasuresLightwardTeamModule]) -> Optional[List[List[Character]]]:
    """
    穷举配队组合
    :param node_combat_types: 节点对应属性
    :param config_module_list: 配队模块列表
    :return: 配队组合
    """
    total_node_cnt: int = len(node_combat_types)
    best_mission_team: Optional[TreasuresLightwardMissionTeam] = None

    # 先排序 保证可以按阶段搜索
    sorted_config_module_list = sorted(config_module_list, key=lambda x: x.module_node_phase)

    def impossibly_greater(current_mission_team: TreasuresLightwardMissionTeam) -> bool:
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

    def dfs(current_mission_team: TreasuresLightwardMissionTeam,
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
    dfs(TreasuresLightwardMissionTeam(node_combat_types), 0)  # 搜索
    log.info('组合配队完成 耗时 %.2f秒', time.time() - start_time)

    if best_mission_team is None:
        return None
    else:
        return best_mission_team.character_list

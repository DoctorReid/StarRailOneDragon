import time
from typing import List, Optional

from basic.i18_utils import gt
from basic.log_utils import log
from sr.const.character_const import get_character_by_id, Character, TECHNIQUE_BUFF, TECHNIQUE_ATTACK, \
    TECHNIQUE_BUFF_ATTACK, is_attack_character, SILVERWOLF, CharacterTechniqueType
from sr.context import Context
from sr.operation import Operation, OperationOneRoundResult
from sr.operation.unit.get_team_member_in_world import GetTeamMemberInWorld


class EnterFightInForgottenHall(Operation):

    def __init__(self, ctx: Context, character_list: Optional[List[Character]] = None):
        """
        需要在忘却之庭节点内 靠近敌人 在准备开始战斗前使用
        上BUFF之后进入战斗
        优先使用上BUFF不触发战斗的秘技 最后再使用开战技能
        :param ctx:
        :param character_list: 当前配队 无传入时自动识别 但不准
        """
        super().__init__(ctx, op_name=gt('忘却之庭 使用秘技并进入战斗', 'ui'))
        self.phase: int = 0
        self.character_list_from_param: Optional[List[Character]] = character_list
        self.character_list: List[Character] = []
        self.technique_order: List[int] = []
        self.need_attack_finally: bool = False  # 最后需要攻击

    def _init_before_execute(self):
        """
        执行前的初始化 注意初始化要全面 方便一个指令重复使用
        """
        super()._init_before_execute()
        self.character_list = []
        self.technique_order = []
        self.need_attack_finally = False

    def _execute_one_round(self) -> OperationOneRoundResult:
        if self.phase == 0:  # 判断当前角色
            self._get_character_list()
            self._get_technique_order()
            self.phase += 1
            return Operation.round_wait()
        elif self.phase == 1:  # 使用秘技
            self._use_technique()
            self.phase += 1
            return Operation.round_wait()
        elif self.phase == 2:  # 发起攻击
            self._attack()
            return Operation.round_success()

    def _get_character_list(self):
        """
        获取当前队伍的角色
        :return:
        """
        if self.character_list_from_param is None:
            for i in range(4):
                op = GetTeamMemberInWorld(self.ctx, i + 1)
                op_result = op.execute()
                character: Optional[Character] = None
                if op_result.success:
                    character = get_character_by_id(op_result.status)
                self.character_list.append(character)
        else:
            for c in self.character_list_from_param:
                self.character_list.append(c)

    def _get_technique_order(self):
        """
        根据当前队伍的角色 获取施放秘技的顺序
        :return:
        """
        for i in range(4):  # 优先使用普通BUFF
            if self.character_list[i] is None:
                continue
            if self.character_list[i].technique_type == TECHNIQUE_BUFF:
                self.technique_order.append(i)

        for i in range(4):  # 输出位攻击类
            if self.character_list[i] is None:
                continue
            if not is_attack_character(self.character_list[i].id):
                continue
            if self.character_list[i].technique_type in (TECHNIQUE_ATTACK, TECHNIQUE_BUFF_ATTACK):
                self.technique_order.append(i)
                return

        for i in range(4):  # 银狼攻击
            if self.character_list[i] is None:
                continue
            if self.character_list[i] == SILVERWOLF:
                self.technique_order.append(i)
                self.finish_tech_type = TECHNIQUE_ATTACK
                return

        for i in range(4):  # 普通攻击
            if self.character_list[i] is None:
                continue
            if self.character_list[i].technique_type in (TECHNIQUE_ATTACK, TECHNIQUE_BUFF_ATTACK):
                self.technique_order.append(i)
                return

    def _use_technique(self):
        """
        按顺序使用秘技
        :return:
        """
        log.info('准备使用秘技 当前配队 %s', [i.cn for i in self.character_list])
        for idx in self.technique_order:
            self._use_technique_by_one(idx)
            character = self.character_list[idx]
            self.need_attack_finally = character.technique_type != TECHNIQUE_ATTACK

    def _use_technique_by_one(self, idx):
        """
        切换角色并使用秘技
        :param idx:
        :return:
        """
        self.ctx.controller.switch_character(idx + 1)
        time.sleep(1)
        self.ctx.controller.use_technique()
        time.sleep(2)

    def _attack(self):
        """
        发起攻击
        :return:
        """
        if not self.need_attack_finally:
            return

        self.ctx.controller.initiate_attack()
        time.sleep(0.5)
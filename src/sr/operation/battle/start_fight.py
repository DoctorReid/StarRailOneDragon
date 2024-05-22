import time
from typing import Optional, List, ClassVar

from basic.i18_utils import gt
from basic.log_utils import log
from sr.const.character_const import Character, get_character_by_id, TECHNIQUE_BUFF, is_attack_character, \
    TECHNIQUE_ATTACK, TECHNIQUE_BUFF_ATTACK, SILVERWOLF, TECHNIQUE_AREA
from sr.context import Context
from sr.image.sceenshot import screen_state
from sr.operation import Operation, OperationOneRoundResult, StateOperation, StateOperationNode, StateOperationEdge
from sr.operation.unit.team import GetTeamMemberInWorld, SwitchMember
from sr.operation.unit.technique import UseTechnique, CheckTechniquePoint, UseTechniqueResult


class Attack(Operation):
    """
    空地上发起一次攻击
    """

    def __init__(self, ctx: Context):
        super().__init__(ctx, op_name=gt('发起一次攻击', 'ui'), timeout_seconds=10)

    def _execute_one_round(self) -> OperationOneRoundResult:
        self.ctx.controller.initiate_attack()  # 主动攻击
        return self.round_success(wait=0.25)


class StartFight(Operation):
    """
    空地上攻击 尝试发动攻击
    """

    def __init__(self, ctx: Context):
        super().__init__(ctx, op_name=gt('主动攻击进入战斗', 'ui'), timeout_seconds=10)

    def _init_before_execute(self):
        super()._init_before_execute()

    def _execute_one_round(self) -> int:
        screen = self.screenshot()

        if not screen_state.is_normal_in_world(screen, self.ctx.im):  # 在战斗界面
            return Operation.SUCCESS

        self.ctx.controller.initiate_attack()  # 主动攻击
        time.sleep(0.5)

        return Operation.WAIT


class StartFightForElite(StateOperation):

    STATUS_DONE: ClassVar[str] = '使用完毕'

    def __init__(self, ctx: Context,
                 character_list: Optional[List[Character]] = None,
                 skip_point_check: bool = False,
                 skip_resurrection_check: bool = False):
        """
        对不会主动攻击的精英怪开战 上BUFF之后进入战斗
        优先使用上BUFF不触发战斗的秘技 最后再使用开战技能
        适用于
        - 逐光捡金
        - 模拟宇宙 精英怪
        :param ctx:
        :param character_list: 当前配队 无传入时自动识别 但不准
        :param skip_point_check: 跳过使用秘技时检测秘技点 逐光捡金可用
        :param skip_resurrection_check: 跳过切换角色时检测复活 逐光捡金可用
        """
        edges: List[StateOperationEdge] = []

        character = StateOperationNode('获取角色列表', self._get_character_list)
        technique_order = StateOperationNode('获取施放顺序', self._get_technique_order)
        edges.append(StateOperationEdge(character, technique_order))

        technique_point = StateOperationNode('检测秘技点', self._check_technique_point)
        edges.append(StateOperationEdge(technique_order, technique_point))

        switch = StateOperationNode('切换角色', self._switch_member)
        edges.append(StateOperationEdge(technique_point, switch))

        use = StateOperationNode('施放秘技', self._use_technique)
        edges.append(StateOperationEdge(switch, use))
        edges.append(StateOperationEdge(use, switch))

        attack = StateOperationNode('攻击', self._attack)
        edges.append(StateOperationEdge(switch, attack, status=StartFightForElite.STATUS_DONE))

        super().__init__(ctx,
                         try_times=5,
                         op_name=gt('使用秘技 进入战斗', 'ui'),
                         edges=edges)
        self.character_list_from_param: Optional[List[Character]] = character_list
        self.character_list: List[Character] = []
        self.technique_order: List[int] = []
        self.need_attack_finally: bool = True  # 最后需要攻击
        self.skip_point_check: bool = skip_point_check  # 跳过检测秘技点
        self.technique_point: int = 5  # 秘技点
        self.technique_idx: int = 0  # 当前到哪一个角色使用
        self.skip_resurrection_check: bool = skip_resurrection_check  # 跳过切换角色时检测复活

    def _init_before_execute(self):
        """
        执行前的初始化 注意初始化要全面 方便一个指令重复使用
        """
        super()._init_before_execute()
        self.character_list = []
        self.technique_order = []
        self.need_attack_finally = True
        self.technique_idx: int = 0  # 当前到哪一个角色使用

    def _check_technique_point(self) -> OperationOneRoundResult:
        """
        检测秘技点 并固定
        :return:
        """
        if self.skip_point_check:
            self.technique_point = 5
        else:
            op = CheckTechniquePoint(self.ctx)
            op_result = op.execute()
            if op_result.success:
                self.technique_point = op_result.data
            else:
                self.technique_point = 0  # 识别失败时直接认为是0

        # 秘技点不够的时候 减少使用
        if self.technique_point < len(self.technique_order):
            self.technique_order = self.technique_order[:self.technique_point]

        log.info(f'最后秘技顺序 {self.technique_order}')
        return self.round_success()

    def _get_character_list(self) -> OperationOneRoundResult:
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

        return self.round_success()

    def _get_technique_order(self) -> OperationOneRoundResult:
        """
        根据当前队伍的角色 获取施放秘技的顺序
        :return:
        """
        for i in range(4):  # 优先使用普通BUFF 无冲突可叠加的
            if self.character_list[i] is None:
                continue
            if self.character_list[i].technique_type == TECHNIQUE_BUFF:
                self.technique_order.append(i)

        for i in range(4):  # 使用结界类 只能一个
            if self.character_list[i] is None:
                continue
            if self.character_list[i].technique_type == TECHNIQUE_AREA:
                self.technique_order.append(i)
                break

        # 任何攻击类只能有一个 选择之后就可以返回了
        for i in range(4):  # 输出位攻击类
            if self.character_list[i] is None:
                continue
            if not is_attack_character(self.character_list[i].id):
                continue
            if self.character_list[i].technique_type in (TECHNIQUE_ATTACK, TECHNIQUE_BUFF_ATTACK):
                self.technique_order.append(i)
                return self.round_success()

        for i in range(4):  # 银狼攻击
            if self.character_list[i] is None:
                continue
            if self.character_list[i] == SILVERWOLF:
                self.technique_order.append(i)
                self.finish_tech_type = TECHNIQUE_ATTACK
                return self.round_success()

        for i in range(4):  # 普通攻击
            if self.character_list[i] is None:
                continue
            if self.character_list[i].technique_type in (TECHNIQUE_ATTACK, TECHNIQUE_BUFF_ATTACK):
                self.technique_order.append(i)
                return self.round_success()

        # 可能存在没有攻击类的角色 此时也需要兜底返回
        return self.round_success()

    def _switch_member(self) -> OperationOneRoundResult:
        """
        切换角色
        :return:
        """
        if self.technique_idx >= len(self.technique_order):
            return self.round_success(StartFightForElite.STATUS_DONE)
        idx = self.technique_order[self.technique_idx]  # 从0开始
        op = SwitchMember(self.ctx, idx + 1, skip_first_screen_check=True,
                          skip_resurrection_check=self.skip_resurrection_check)
        return self.round_by_op(op.execute())

    def _use_technique(self) -> OperationOneRoundResult:
        """
        使用秘技
        :return:
        """
        op = UseTechnique(self.ctx)
        op_result = op.execute()
        use_tech = False
        if op_result.success:
            op_result_data: UseTechniqueResult = op_result.data
            use_tech = op_result_data.use_tech
            idx = self.technique_order[self.technique_idx]
            self.need_attack_finally = self.character_list[idx].technique_type != TECHNIQUE_ATTACK
        self.technique_idx += 1

        wait_time = 0
        if self.technique_idx < len(self.technique_order) and use_tech:
            # 还需要切换人物使用秘技的情况
            # 如果这次使用了秘技 要等待一下后摇消失后 再进行下一步操作
            wait_time = 1.5
        return self.round_by_op(op_result, wait=wait_time)

    def _attack(self) -> OperationOneRoundResult:
        """
        发起攻击
        :return:
        """
        screen = self.screenshot()
        # 仍在大世界的话 就尝试攻击
        if screen_state.is_normal_in_world(screen, self.ctx.im) \
                or screen_state.is_mission_in_world(screen, self.ctx.im):
            self.ctx.controller.initiate_attack()
            self.save_screenshot()
            return self.round_retry('未进入战斗 尝试攻击', wait=1)
        else:
            return self.round_success()

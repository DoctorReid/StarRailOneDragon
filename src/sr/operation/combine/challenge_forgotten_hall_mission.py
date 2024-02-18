from typing import List, Callable, Optional

from basic.i18_utils import gt
from sr.const.character_const import Character
from sr.context import Context
from sr.operation import Operation, OperationSuccess, OperationResult
from sr.operation.combine import StatusCombineOperation2, \
    StatusCombineOperationEdge2, StatusCombineOperationNode
from sr.operation.unit.forgotten_hall.check_mission_star import CheckMissionStar
from sr.operation.unit.forgotten_hall.choose_mission import ChooseMission
from sr.operation.unit.forgotten_hall.choose_team_in_fh import ChooseTeamInForgottenHall
from sr.operation.unit.forgotten_hall.click_challenge_in_forgotten_hall import ClickChallengeInForgottenHall
from sr.operation.unit.forgotten_hall.wait_in_hall import WaitInHall
from sr.screen_area.screen_treasures_lightward import ScreenTreasuresLightWard
from sr.treasures_lightward.op.tl_battle import TlNodeFight, TlAfterNodeFight
from sr.treasures_lightward.treasures_lightward_const import TreasuresLightwardTypeEnum


class ChallengeForgottenHallMission(StatusCombineOperation2):

    def __init__(self, ctx: Context, schedule_type: TreasuresLightwardTypeEnum,
                 mission_num: int, node_cnt: int,
                 cal_team_func: Callable,
                 op_callback: Optional[Callable[[OperationResult], None]] = None
                 ):
        """
        需要已经在逐光捡金选择关卡的页面
        选择目标关卡并挑战
        最后返回状态为星数
        :param ctx: 上下文
        :param mission_num: 关卡编号
        :param node_cnt: 节点数量
        :param cal_team_func:
        """
        edges: List[StatusCombineOperationEdge2] = []

        wait_in_hall = StatusCombineOperationNode('等待逐光捡金界面', WaitInHall(ctx))

        check_star = StatusCombineOperationNode('检查星数', CheckMissionStar(ctx, mission_num))
        edges.append(StatusCombineOperationEdge2(wait_in_hall, check_star))

        full_star = StatusCombineOperationNode('满星结束', OperationSuccess(ctx, '3'))
        edges.append(StatusCombineOperationEdge2(check_star, full_star, status='3'))  # 3颗满了就可以跳过本次挑战了

        enter_mission = StatusCombineOperationNode('选择关卡', ChooseMission(ctx, mission_num))
        edges.append(StatusCombineOperationEdge2(check_star, enter_mission, ignore_status=True))  # 未满星就进行挑战

        choose_team = StatusCombineOperationNode('选择配队角色', ChooseTeamInForgottenHall(ctx, cal_team_func, self._on_team_calculated))
        edges.append(StatusCombineOperationEdge2(enter_mission, choose_team))

        click_challenge = StatusCombineOperationNode('点击【回忆】', ClickChallengeInForgottenHall(ctx))
        edges.append(StatusCombineOperationEdge2(choose_team, click_challenge))

        back_to_hall = StatusCombineOperationNode('战斗结算后返回', TlAfterNodeFight(ctx, schedule_type))

        last_op = click_challenge
        for i in range(node_cnt):
            node_fight = StatusCombineOperationNode('节点战斗 %d' % i, op_func=self.node_fight_op)
            edges.append(StatusCombineOperationEdge2(last_op, node_fight, ignore_status=True))  # 进入下一个节点战斗

            # 无论出现 挑战成功 还是 战斗失败 都是返回
            edges.append(StatusCombineOperationEdge2(node_fight, back_to_hall, status=ScreenTreasuresLightWard.AFTER_BATTLE_SUCCESS_1.value.text))
            edges.append(StatusCombineOperationEdge2(node_fight, back_to_hall, status=ScreenTreasuresLightWard.AFTER_BATTLE_FAIL.value.text))
            last_op = node_fight

        check_star_2 = StatusCombineOperationNode('挑战后再检查星数', CheckMissionStar(ctx, mission_num))
        edges.append(StatusCombineOperationEdge2(back_to_hall, check_star_2))

        super().__init__(ctx, op_name='%s %d' % (gt('逐光捡金 挑战关卡'), mission_num),
                         edges=edges, op_callback=op_callback)

        self.teams: Optional[List[List[Character]]] = None
        """各个节点的配队"""
        self.current_node_idx: int = 0
        """当前进行的节点"""

    def _init_before_execute(self):
        """
        执行前的初始化 注意初始化要全面 方便一个指令重复使用
        """
        super()._init_before_execute()
        self.teams = None
        self.current_node_idx = 0

    def _on_team_calculated(self, teams: List[List[Character]]):
        """
        更新配队
        :param teams:
        :return:
        """
        self.teams = teams

    def node_fight_op(self) -> Operation:
        """
        生成节点战斗的指令 会根据组队情况返回
        :return:
        """
        idx = self.current_node_idx
        team = None if self.teams is None or idx >= len(self.teams) else self.teams[idx]
        return TlNodeFight(self.ctx, idx == 0, team=team, op_callback=self._after_node)

    def _after_node(self, op_result: OperationResult):
        """
        节点完成后的回调
        :return:
        """
        self.current_node_idx += 1

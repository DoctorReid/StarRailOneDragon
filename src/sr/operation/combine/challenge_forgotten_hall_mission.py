from typing import List, Callable

from basic.i18_utils import gt
from sr.context import Context
from sr.operation import Operation, OperationSuccess
from sr.operation.combine import StatusCombineOperation, StatusCombineOperationEdge
from sr.operation.combine.node_fight import NodeFight
from sr.operation.unit.forgotten_hall.after_fight_to_hall import AfterFightToHall
from sr.operation.unit.forgotten_hall.auto_fight_in_forgotten_hall import AutoFightInForgottenHall
from sr.operation.unit.forgotten_hall.check_mission_star import CheckMissionStar
from sr.operation.unit.forgotten_hall.choose_mission import ChooseMission
from sr.operation.unit.forgotten_hall.choose_team_in_fh import ChooseTeamInForgottenHall
from sr.operation.unit.forgotten_hall.click_challenge_in_forgotten_hall import ClickChallengeInForgottenHall


class ChallengeForgottenHallMission(StatusCombineOperation):

    def __init__(self, ctx: Context, mission_num: int, node_cnt: int,
                 mission_star_callback: Callable,
                 cal_team_func: Callable):
        """
        需要已经在忘却之庭选择关卡的页面
        选择目标关卡并挑战
        最后返回状态为星数
        :param ctx: 上下文
        :param mission_num: 关卡编号
        :param node_cnt: 节点数量
        :param mission_star_callback: 获取到的关卡星数回调
        :param cal_team_func:
        """

        ops: List[Operation] = []
        edges: List[StatusCombineOperationEdge] = []

        check_star = CheckMissionStar(ctx, mission_num, mission_star_callback)  # 检查星数
        ops.append(check_star)

        full_star = OperationSuccess(ctx, '3')  # 满星
        ops.append(full_star)
        edges.append(StatusCombineOperationEdge(op_from=check_star, op_to=full_star, status='3'))  # 3颗满了就可以跳过本次挑战了

        enter_mission = ChooseMission(ctx, mission_num)  # 选择关卡
        ops.append(enter_mission)
        edges.append(StatusCombineOperationEdge(op_from=check_star, op_to=enter_mission, ignore_status=True))  # 未满星就进行挑战

        choose_team = ChooseTeamInForgottenHall(ctx, cal_team_func)  # 选择配队角色
        ops.append(choose_team)
        edges.append(StatusCombineOperationEdge(op_from=enter_mission, op_to=choose_team))

        click_challenge = ClickChallengeInForgottenHall(ctx)  # 点击【回忆】
        ops.append(click_challenge)
        edges.append(StatusCombineOperationEdge(op_from=choose_team, op_to=click_challenge))

        back_to_hall = AfterFightToHall(ctx)  # 战斗结算后返回
        ops.append(back_to_hall)

        last_op = click_challenge
        for i in range(node_cnt):
            node_fight = NodeFight(ctx, i == 0)
            ops.append(node_fight)
            edges.append(StatusCombineOperationEdge(last_op, node_fight, ignore_status=True))  # 节点战斗

            edges.append(StatusCombineOperationEdge(node_fight, back_to_hall, status=AutoFightInForgottenHall.BATTLE_FAIL_STATUS))  # 失败
            edges.append(StatusCombineOperationEdge(node_fight, back_to_hall, status=AutoFightInForgottenHall.BATTLE_SUCCESS_STATUS))  # 成功
            last_op = node_fight

        check_star_2 = CheckMissionStar(ctx, mission_num, mission_star_callback)  # 挑战后再检查星数
        ops.append(check_star_2)
        edges.append(StatusCombineOperationEdge(back_to_hall, check_star_2))

        super().__init__(ctx, ops, edges, op_name='%s %d' % (gt('忘却之庭 挑战关卡'), mission_num))

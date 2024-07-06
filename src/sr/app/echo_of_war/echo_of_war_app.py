from typing import Optional, List

from cv2.typing import MatLike

from basic import str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr.app.app_run_record import AppRunRecord
from sr.app.application_base import Application
from sr.app.echo_of_war.echo_of_war_config import EchoOfWarPlanItem
from sr.app.echo_of_war.echo_of_war_run_record import EchoOfWarRunRecord
from sr.context.context import Context
from sr.image.sceenshot import large_map
from sr.interastral_peace_guide.guide_const import GuideMission, GuideMissionEnum
from sr.operation import StateOperationEdge, StateOperationNode, OperationOneRoundResult
from sr.operation.battle.challenge_ehco_of_war import ChallengeEchoOfWar
from sr.operation.common.back_to_normal_world_plus import BackToNormalWorldPlus
from sr.operation.common.cancel_mission_trace import CancelMissionTrace
from sr.operation.unit.open_map import OpenMap


class EchoOfWarApp(Application):

    def __init__(self, ctx: Context):
        edges: List[StateOperationEdge] = []

        world = StateOperationNode('返回大世界', op=BackToNormalWorldPlus(ctx))

        cancel_trace = StateOperationNode('取消任务追踪', op=CancelMissionTrace(ctx))
        edges.append(StateOperationEdge(world, cancel_trace))

        open_map = StateOperationNode('打开地图', op=OpenMap(ctx))
        edges.append(StateOperationEdge(cancel_trace, open_map))

        check_power = StateOperationNode('检查体力', self._check_power)
        edges.append(StateOperationEdge(open_map, check_power))

        use = StateOperationNode('挑战', self._use_power)
        edges.append(StateOperationEdge(check_power, use))

        super().__init__(ctx, op_name=gt('历战余响', 'ui'),
                         run_record=ctx.echo_run_record,
                         edges=edges
                         )
        self.power: int = 0

    def _check_power(self) -> OperationOneRoundResult:
        screen: MatLike = self.screenshot()
        part, _ = cv2_utils.crop_image(screen, large_map.LARGE_MAP_POWER_RECT)
        ocr_result = self.ctx.ocr.ocr_for_single_line(part, strict_one_line=True)
        self.power = str_utils.get_positive_digits(ocr_result)
        log.info('当前体力 %d', self.power)
        return self.round_success()

    def _use_power(self) -> OperationOneRoundResult:
        config = self.ctx.echo_config
        config.check_plan_finished()
        plan: Optional[EchoOfWarPlanItem] = config.next_plan_item
        if plan is None:
            return self.round_success('无挑战计划')
        mission: Optional[GuideMission] = GuideMissionEnum.get_by_unique_id(plan['mission_id'])

        run_times: int = self.power // mission.power

        record: EchoOfWarRunRecord = self.ctx.echo_run_record
        if record.left_times < run_times:
            run_times = record.left_times

        if run_times == 0:
            return self.round_success('无足够体力')

        if run_times + plan['run_times'] > plan['plan_times']:
            run_times = plan['plan_times'] - plan['run_times']

        def on_battle_success(run_times: int, use_power: int):
            self.power -= use_power
            log.info('运行次数 %d, 消耗体力: %d, 剩余体力: %d', run_times, use_power, self.power)
            plan['run_times'] += run_times
            log.info('副本完成次数: %d, 计划次数: %d', plan['run_times'], plan['plan_times'])
            record.left_times = record.left_times - run_times
            log.info('本周历战余响剩余次数: %d', record.left_times)
            config.save()
            record.update_status(AppRunRecord.STATUS_RUNNING)

        op = ChallengeEchoOfWar(self.ctx, mission, plan['team_num'], run_times,
                                support=plan['support'] if plan['support'] != 'none' else None,
                                on_battle_success=on_battle_success)
        if op.execute().success:
            return self.round_wait()
        else:  # 挑战
            return self.round_retry('挑战失败')

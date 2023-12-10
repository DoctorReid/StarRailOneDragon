from typing import Optional

from basic.i18_utils import gt
from sr.app import Application, AppRunRecord, AppDescription, register_app
from sr.const import phone_menu_const
from sr.const.traing_mission_const import MISSION_SALVAGE_RELIC, MISSION_DESTRUCTIBLE_OBJECTS
from sr.context import Context
from sr.operation import Operation, OperationSuccess, OperationOneRoundResult
from sr.operation.combine import StatusCombineOperationEdge, StatusCombineOperation
from sr.operation.combine.destory_objects import DestroyObjects
from sr.operation.combine.salvage_relic import SalvageRelic
from sr.operation.unit.guide import GUIDE_TAB_2
from sr.operation.unit.guide.choose_guide_tab import ChooseGuideTab
from sr.operation.unit.guide.claim_training_reward import ClaimTrainingReward
from sr.operation.unit.guide.claim_training_score import ClaimTrainingScore
from sr.operation.unit.guide.get_training_score import GetTrainingScore
from sr.operation.unit.guide.get_training_unfinished_mission import GetTrainingUnfinishedMission
from sr.operation.unit.menu.click_phone_menu_item import ClickPhoneMenuItem
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu

DAILY_TRAINING = AppDescription(cn='每日实训', id='daily_training')
register_app(DAILY_TRAINING)


class DailyTrainingRecord(AppRunRecord):

    def __init__(self):
        super().__init__(DAILY_TRAINING.id)

    def reset_record(self):
        """
        运行记录重置 非公共部分由各app自行实现
        :return:
        """
        super().reset_record()
        self.score = 0

    @property
    def score(self) -> int:
        return self.get('score', 0)

    @score.setter
    def score(self, new_value: int):
        self.update('score', new_value)


_daily_training_record: Optional[DailyTrainingRecord] = None


def get_record() -> DailyTrainingRecord:
    global _daily_training_record
    if _daily_training_record is None:
        _daily_training_record = DailyTrainingRecord()
    return _daily_training_record


class DailyTrainingApp(Application):

    run_record: DailyTrainingRecord

    def __init__(self, ctx: Context):
        super().__init__(ctx,
                         op_name='%s %s' % (gt('每日实训', 'ui'), gt('应用', 'ui')),
                         run_record=get_record())

        self.phase: int = 0
        self.op: Operation = OperationSuccess(ctx)

    def _init_before_execute(self):
        super()._init_before_execute()
        self.phase = 0

        ops = []
        edges = []

        open_menu = OpenPhoneMenu(self.ctx)  # 打开菜单
        ops.append(open_menu)

        click_guide = ClickPhoneMenuItem(self.ctx, phone_menu_const.INTERASTRAL_GUIDE)  # 点击【指南】
        ops.append(click_guide)
        edges.append(StatusCombineOperationEdge(open_menu, click_guide))

        choose_daily_training = ChooseGuideTab(self.ctx, GUIDE_TAB_2)  # 选择每日实训
        ops.append(choose_daily_training)
        edges.append(StatusCombineOperationEdge(click_guide, choose_daily_training))

        claim_score = ClaimTrainingScore(self.ctx)  # 领取分数
        ops.append(claim_score)
        edges.append(StatusCombineOperationEdge(choose_daily_training, claim_score))

        check_score = GetTrainingScore(self.ctx, score_callback=self._update_training_score)  # 检查目前点数
        ops.append(check_score)
        edges.append(StatusCombineOperationEdge(claim_score, check_score))

        final_claim_reward = ClaimTrainingReward(self.ctx)  # 领取奖励
        ops.append(final_claim_reward)
        edges.append(StatusCombineOperationEdge(check_score, final_claim_reward, status='500'))  # 满分退出

        back_to = OpenPhoneMenu(self.ctx)  # 返回菜单
        ops.append(back_to)
        edges.append(StatusCombineOperationEdge(final_claim_reward, back_to))

        get_mission = GetTrainingUnfinishedMission(self.ctx)  # 获取一个可执行的任务
        ops.append(get_mission)
        edges.append(StatusCombineOperationEdge(check_score, get_mission, ignore_status=True))

        salvage_relic = SalvageRelic(self.ctx)  # 遗器分解
        ops.append(salvage_relic)
        edges.append(StatusCombineOperationEdge(get_mission, salvage_relic, status=MISSION_SALVAGE_RELIC.id_cn))
        edges.append(StatusCombineOperationEdge(salvage_relic, back_to, success=False))  # 执行失败
        edges.append(StatusCombineOperationEdge(salvage_relic, open_menu))  # 执行成功 从头开始

        destroy_objects = DestroyObjects(self.ctx)  # 可破坏物
        ops.append(destroy_objects)
        edges.append(StatusCombineOperationEdge(get_mission, destroy_objects, status=MISSION_DESTRUCTIBLE_OBJECTS.id_cn))
        edges.append(StatusCombineOperationEdge(destroy_objects, final_claim_reward, success=False))  # 执行失败
        edges.append(StatusCombineOperationEdge(destroy_objects, open_menu))  # 执行成功 从头开始

        self.op = StatusCombineOperation(self.ctx, ops, edges, start_op=open_menu,
                                         op_name='%s %s' % (gt('每日实训', 'ui'), gt('执行', 'ui')))

    def _execute_one_round(self) -> OperationOneRoundResult:
        op_result = self.op.execute()
        if op_result.success:
            return Operation.round_success(op_result.status)
        else:
            return Operation.round_retry(op_result.status)

    def _update_training_score(self, score: int):
        """
        更新每日实训点数
        :param score: 分数
        :return:
        """
        self.run_record.score = score

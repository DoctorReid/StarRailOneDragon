from typing import Optional, List

from basic.i18_utils import gt
from sr.app import Application, AppRunRecord, AppDescription, register_app, Application2
from sr.const import phone_menu_const
from sr.const.traing_mission_const import MISSION_SALVAGE_RELIC, MISSION_DESTRUCTIBLE_OBJECTS, MISSION_USE_TECHNIQUE, \
    MISSION_DAILY_MISSION, MISSION_TAKE_PHOTO, MISSION_SYNTHESIZE_CONSUMABLE
from sr.context import Context
from sr.operation import Operation, OperationSuccess, OperationOneRoundResult
from sr.operation.combine import StatusCombineOperationEdge, StatusCombineOperation, StatusCombineOperationNode, \
    StatusCombineOperationEdge2
from sr.operation.combine.destory_objects import DestroyObjects
from sr.operation.combine.dt_synthesize_consumable import DtSynthesizeConsumable
from sr.operation.combine.dt_take_photo import DtTakePhoto
from sr.operation.combine.dt_use_2_technique import Use2Technique
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


class DailyTrainingApp(Application2):

    run_record: DailyTrainingRecord

    def __init__(self, ctx: Context):
        edges: List[StatusCombineOperationEdge2] = []

        open_menu = StatusCombineOperationNode(node_id='open_menu', op=OpenPhoneMenu(ctx))  # 打开菜单
        click_guide = StatusCombineOperationNode(node_id='click_guide', op=ClickPhoneMenuItem(ctx, phone_menu_const.INTERASTRAL_GUIDE))  # 点击【指南】
        edges.append(StatusCombineOperationEdge2(node_from=open_menu, node_to=click_guide))

        choose_daily_training = StatusCombineOperationNode(node_id='choose_daily_training', op=ChooseGuideTab(ctx, GUIDE_TAB_2))  # 选择每日实训
        edges.append(StatusCombineOperationEdge2(node_from=click_guide, node_to=choose_daily_training))

        claim_score = StatusCombineOperationNode(node_id='claim_score', op=ClaimTrainingScore(ctx))  # 领取分数
        edges.append(StatusCombineOperationEdge2(node_from=choose_daily_training, node_to=claim_score))

        check_score = StatusCombineOperationNode(node_id='check_score', op=GetTrainingScore(ctx, score_callback=self._update_training_score))  # 检查目前点数
        edges.append(StatusCombineOperationEdge2(node_from=claim_score, node_to=check_score))

        final_claim_reward = StatusCombineOperationNode(node_id='final_claim_reward', op=ClaimTrainingReward(ctx))  # 领取奖励
        edges.append(StatusCombineOperationEdge2(node_from=check_score, node_to=final_claim_reward, status='500'))  # 满分退出

        back_to = StatusCombineOperationNode(node_id='back_to', op=OpenPhoneMenu(ctx))  # 返回菜单
        edges.append(StatusCombineOperationEdge2(node_from=final_claim_reward, node_to=back_to))

        get_mission = StatusCombineOperationNode(node_id='get_mission', op=GetTrainingUnfinishedMission(ctx))  # 获取一个可执行的任务
        edges.append(StatusCombineOperationEdge2(node_from=check_score, node_to=get_mission, ignore_status=True))

        edges.append(StatusCombineOperationEdge2(node_from=get_mission, node_to=final_claim_reward, success=False, ignore_status=True))  # 没有可执行的任务

        salvage_relic = StatusCombineOperationNode(node_id='salvage_relic', op=SalvageRelic(ctx))  # 遗器分解
        edges.append(StatusCombineOperationEdge2(node_from=get_mission, node_to=salvage_relic, status=MISSION_SALVAGE_RELIC.id_cn))
        edges.append(StatusCombineOperationEdge2(node_from=salvage_relic, node_to=back_to, success=False))  # 执行失败
        edges.append(StatusCombineOperationEdge2(node_from=salvage_relic, node_to=open_menu))  # 执行成功 从头开始

        destroy_objects = StatusCombineOperationNode(node_id='destroy_objects', op=DestroyObjects(ctx))  # 可破坏物
        edges.append(StatusCombineOperationEdge2(node_from=get_mission, node_to=destroy_objects, status=MISSION_DESTRUCTIBLE_OBJECTS.id_cn))
        edges.append(StatusCombineOperationEdge2(node_from=destroy_objects, node_to=final_claim_reward, success=False))  # 执行失败
        edges.append(StatusCombineOperationEdge2(node_from=destroy_objects, node_to=open_menu))  # 执行成功 从头开始

        use_2_technique = StatusCombineOperationNode(node_id='use_2_technique', op=Use2Technique(ctx))  # 施放秘技
        edges.append(StatusCombineOperationEdge2(node_from=get_mission, node_to=use_2_technique, status=MISSION_USE_TECHNIQUE.id_cn))
        edges.append(StatusCombineOperationEdge2(node_from=use_2_technique, node_to=final_claim_reward, success=False))  # 执行失败
        edges.append(StatusCombineOperationEdge2(node_from=use_2_technique, node_to=open_menu))  # 执行成功 从头开始

        take_photo = StatusCombineOperationNode(node_id='take_photo', op=DtTakePhoto(ctx))  # 拍照
        edges.append(StatusCombineOperationEdge2(node_from=get_mission, node_to=take_photo, status=MISSION_TAKE_PHOTO.id_cn))
        edges.append(StatusCombineOperationEdge2(node_from=take_photo, node_to=final_claim_reward, success=False))  # 执行失败
        edges.append(StatusCombineOperationEdge2(node_from=take_photo, node_to=open_menu))  # 执行成功 从头开始

        synthesize_consumable = StatusCombineOperationNode('合成消耗品', DtSynthesizeConsumable(ctx))
        edges.append(StatusCombineOperationEdge2(node_from=get_mission, node_to=synthesize_consumable, status=MISSION_SYNTHESIZE_CONSUMABLE.id_cn))
        edges.append(StatusCombineOperationEdge2(node_from=synthesize_consumable, node_to=final_claim_reward, success=False))  # 执行失败
        edges.append(StatusCombineOperationEdge2(node_from=synthesize_consumable, node_to=open_menu))  # 执行成功 从头开始

        super().__init__(ctx,
                         op_name='%s %s' % (gt('每日实训', 'ui'), gt('应用', 'ui')),
                         run_record=get_record(),
                         edges=edges,
                         specified_start_node=open_menu)

    def _update_training_score(self, score: int):
        """
        更新每日实训点数
        :param score: 分数
        :return:
        """
        self.run_record.score = score

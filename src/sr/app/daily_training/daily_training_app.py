from typing import List

from basic.i18_utils import gt
from sr.app.application_base import Application2
from sr.const import phone_menu_const
from sr.const.traing_mission_const import MISSION_SALVAGE_RELIC, MISSION_DESTRUCTIBLE_OBJECTS, MISSION_USE_TECHNIQUE, \
    MISSION_TAKE_PHOTO, MISSION_SYNTHESIZE_CONSUMABLE
from sr.context import Context
from sr.operation import StateOperationEdge, StateOperationNode
from sr.operation.combine.destory_objects import DestroyObjects
from sr.operation.combine.dt_synthesize_consumable import DtSynthesizeConsumable
from sr.operation.combine.dt_take_photo import DtTakePhoto
from sr.operation.combine.dt_use_2_technique import Use2Technique
from sr.operation.combine.salvage_relic import SalvageRelic
from sr.operation.unit.guide import GuideTabEnum
from sr.operation.unit.guide.choose_guide_tab import ChooseGuideTab
from sr.operation.unit.guide.claim_training_reward import ClaimTrainingReward
from sr.operation.unit.guide.claim_training_score import ClaimTrainingScore
from sr.operation.unit.guide.get_training_score import GetTrainingScore
from sr.operation.unit.guide.get_training_unfinished_mission import GetTrainingUnfinishedMission
from sr.operation.unit.menu.click_phone_menu_item import ClickPhoneMenuItem
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu


class DailyTrainingApp(Application2):

    def __init__(self, ctx: Context):
        edges: List[StateOperationEdge] = []

        open_menu = StateOperationNode('打开菜单', op=OpenPhoneMenu(ctx))
        click_guide = StateOperationNode('点击【指南】', op=ClickPhoneMenuItem(ctx, phone_menu_const.INTERASTRAL_GUIDE))
        edges.append(StateOperationEdge(open_menu, click_guide))

        choose_daily_training = StateOperationNode('选择每日实训', op=ChooseGuideTab(ctx, GuideTabEnum.TAB_2.value))
        edges.append(StateOperationEdge(click_guide, choose_daily_training))

        claim_score = StateOperationNode('领取实训点数', op=ClaimTrainingScore(ctx))
        edges.append(StateOperationEdge(choose_daily_training, claim_score))

        check_score = StateOperationNode('检查目前点数', op=GetTrainingScore(ctx, score_callback=self._update_training_score))
        edges.append(StateOperationEdge(claim_score, check_score))

        final_claim_reward = StateOperationNode('领取奖励', op=ClaimTrainingReward(ctx))
        edges.append(StateOperationEdge(check_score, final_claim_reward, status='500'))  # 满分退出

        back_to = StateOperationNode('返回菜单', op=OpenPhoneMenu(ctx))
        edges.append(StateOperationEdge(final_claim_reward, back_to))

        get_mission = StateOperationNode('获取一个可执行的任务', op=GetTrainingUnfinishedMission(ctx))
        edges.append(StateOperationEdge(check_score, get_mission, ignore_status=True))

        # 没有可执行的任务
        edges.append(StateOperationEdge(get_mission, final_claim_reward, success=False, ignore_status=True))

        salvage_relic = StateOperationNode('遗器分解', op=SalvageRelic(ctx))
        edges.append(StateOperationEdge(get_mission, salvage_relic, status=MISSION_SALVAGE_RELIC.id_cn))
        edges.append(StateOperationEdge(salvage_relic, back_to, success=False))  # 执行失败
        edges.append(StateOperationEdge(salvage_relic, open_menu))  # 执行成功 从头开始

        destroy_objects = StateOperationNode('可破坏物', op=DestroyObjects(ctx))
        edges.append(StateOperationEdge(get_mission, destroy_objects, status=MISSION_DESTRUCTIBLE_OBJECTS.id_cn))
        edges.append(StateOperationEdge(destroy_objects, final_claim_reward, success=False))  # 执行失败
        edges.append(StateOperationEdge(destroy_objects, open_menu))  # 执行成功 从头开始

        use_2_technique = StateOperationNode('施放秘技', op=Use2Technique(ctx))
        edges.append(StateOperationEdge(get_mission, use_2_technique, status=MISSION_USE_TECHNIQUE.id_cn))
        edges.append(StateOperationEdge(use_2_technique, final_claim_reward, success=False))  # 执行失败
        edges.append(StateOperationEdge(use_2_technique, open_menu))  # 执行成功 从头开始

        take_photo = StateOperationNode('拍照', op=DtTakePhoto(ctx))
        edges.append(StateOperationEdge(get_mission, take_photo, status=MISSION_TAKE_PHOTO.id_cn))
        edges.append(StateOperationEdge(take_photo, final_claim_reward, success=False))  # 执行失败
        edges.append(StateOperationEdge(take_photo, open_menu))  # 执行成功 从头开始

        synthesize_consumable = StateOperationNode('合成消耗品', op=DtSynthesizeConsumable(ctx))
        edges.append(StateOperationEdge(get_mission, synthesize_consumable, status=MISSION_SYNTHESIZE_CONSUMABLE.id_cn))
        edges.append(StateOperationEdge(synthesize_consumable, final_claim_reward, success=False))  # 执行失败
        edges.append(StateOperationEdge(synthesize_consumable, open_menu))  # 执行成功 从头开始

        super().__init__(ctx,
                         op_name='%s %s' % (gt('每日实训', 'ui'), gt('应用', 'ui')),
                         run_record=ctx.daily_training_run_record,
                         edges=edges,
                         specified_start_node=open_menu)

    def _update_training_score(self, score: int):
        """
        更新每日实训点数
        :param score: 分数
        :return:
        """
        self.run_record.score = score

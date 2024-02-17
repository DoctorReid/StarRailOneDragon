from typing import Optional, List, ClassVar

from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr.app import Application2, AppRunRecord
from sr.app.treasures_lightward.treasures_lightward_config import TreasuresLightwardConfig, get_config
from sr.app.treasures_lightward.treasures_lightward_record import TreasuresLightwardRecord, get_record, \
    TreasuresLightwardScheduleRecord
from sr.const import phone_menu_const
from sr.const.character_const import CharacterCombatType, Character
from sr.context import Context
from sr.operation import StateOperationEdge, StateOperationNode, OperationResult, OperationOneRoundResult, Operation
from sr.operation.combine.challenge_forgotten_hall_mission import ChallengeForgottenHallMission
from sr.operation.unit.forgotten_hall.check_next_challenge_mission import CheckMaxUnlockMission
from sr.operation.unit.forgotten_hall.get_reward_in_fh import GetRewardInForgottenHall
from sr.operation.unit.guide import GuideTabEnum
from sr.operation.unit.guide.choose_guide_tab import ChooseGuideTab
from sr.operation.unit.menu.click_phone_menu_item import ClickPhoneMenuItem
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu
from sr.screen_area.screen_treasures_lightward import ScreenTreasuresLightWard
from sr.treasures_lightward.op.check_star import TlCheckTotalStar
from sr.treasures_lightward.treasures_lightward_const import TreasuresLightwardTypeEnum
from sr.treasures_lightward.treasures_lightward_team_module import search_best_mission_team


class TreasuresLightwardApp(Application2):

    STATUS_SHOULD_CHALLENGE: ClassVar[str] = '进行挑战'

    def __init__(self, ctx: Context):
        self.run_record: Optional[TreasuresLightwardRecord] = get_record()
        edges: List[StateOperationEdge] = []

        open_menu = StateOperationNode('打开菜单', op=OpenPhoneMenu(ctx))
        choose_guide = StateOperationNode('选择【指南】', op=ClickPhoneMenuItem(ctx, phone_menu_const.INTERASTRAL_GUIDE))
        edges.append(StateOperationEdge(open_menu, choose_guide))

        choose_treasure = StateOperationNode('选择【逐光捡金】', op=ChooseGuideTab(ctx, GuideTabEnum.TAB_4.value))
        edges.append(StateOperationEdge(choose_guide, choose_treasure))

        # 忘却之庭部分指令
        choose_fh = StateOperationNode('选择【忘却之庭】', self._choose_forgotten_hall)
        edges.append(StateOperationEdge(choose_treasure, choose_fh))

        fh_check_record = StateOperationNode('检测【忘却之庭】记录', self._check_record_and_tp)
        edges.append(StateOperationEdge(choose_fh, fh_check_record))

        fh_check_total_star = StateOperationNode('【忘却之庭】检测总星数', self._check_total_star)
        edges.append(StateOperationEdge(fh_check_record, fh_check_total_star, status=TreasuresLightwardApp.STATUS_SHOULD_CHALLENGE))  # 需要进行挑战 检测星数

        fh_finished = StateOperationNode('【忘却之庭】设置完成', self._set_schedule_finished)
        # edges.append(StateOperationEdge(fh_check_total_star, fh_finished, status=TlCheckTotalStar.STATUS_FULL_STAR))  # 满星的时候直接设置为成功

        fh_get_reward = StateOperationNode('【忘却之庭】领取奖励', op=GetRewardInForgottenHall(ctx))
        edges.append(StateOperationEdge(fh_finished, fh_get_reward))

        fh_back_menu = StateOperationNode('【忘却之庭】返回菜单', op=OpenPhoneMenu(ctx))
        edges.append(StateOperationEdge(fh_get_reward, fh_back_menu))
        edges.append(StateOperationEdge(fh_back_menu, choose_guide))  # 继续下一期的挑战

        fh_check_max_unlock = StateOperationNode('【忘却之庭】最大的已解锁关卡', op=CheckMaxUnlockMission(ctx, self._on_max_unlock_done))
        edges.append(StateOperationEdge(fh_check_total_star, fh_check_max_unlock, ignore_status=True))  # 非满星的时候找到开始关卡

        fh_challenge_mission = StateOperationNode('【忘却之庭】挑战关卡', self._challenge_next_mission)
        edges.append(StateOperationEdge(fh_check_max_unlock, fh_challenge_mission))  # 挑战

        edges.append(StateOperationEdge(fh_challenge_mission, fh_challenge_mission, status='3'))  # 循环挑战到满星
        edges.append(StateOperationEdge(fh_challenge_mission, fh_finished, ignore_status=True))  # 没满星就不挑战下一个了

        super().__init__(ctx, op_name=gt('逐光捡金', 'ui'),
                         run_record=self.run_record, edges=edges)

        self.schedule_type: TreasuresLightwardTypeEnum = TreasuresLightwardTypeEnum.FORGOTTEN_HALL  # 当前挑战类型
        self.challenge_schedule: Optional[TreasuresLightwardScheduleRecord] = None  # 当前挑战的期数
        self.config: TreasuresLightwardConfig = get_config()
        self._current_mission_num: int = 1

    def _init_before_execute(self):
        super()._init_before_execute()
        self._current_mission_num = 1

    def _choose_forgotten_hall(self):
        """
        在【指南】-【逐光捡金】画面 选择【忘却之庭】
        :return:
        """
        area = ScreenTreasuresLightWard.TL_CATEGORY_FORGOTTEN_HALL.value
        click = self.find_and_click_area(area)
        if click == Operation.OCR_CLICK_SUCCESS:
            self.schedule_type = TreasuresLightwardTypeEnum.FORGOTTEN_HALL
            return Operation.round_success()
        else:
            return Operation.round_retry('点击%s失败', area.text)

    def _choose_pure_fiction(self):
        """
        在【指南】-【逐光捡金】画面 选择【虚构叙事】
        :return:
        """
        area = ScreenTreasuresLightWard.TL_CATEGORY_PURE_FICTION.value
        click = self.find_and_click_area(area)
        if click == Operation.OCR_CLICK_SUCCESS:
            self.schedule_type = TreasuresLightwardTypeEnum.PURE_FICTION
            return Operation.round_success(wait=1)
        else:
            return Operation.round_retry('点击%s失败', area.text)

    def _check_record_and_tp(self):
        """
        在【指南】-【逐光捡金】画面 检查对应排期的运行记录 并传送到一个没有完成挑战的
        :return:
        """
        screen = self.screenshot()
        tp_area_list = [ScreenTreasuresLightWard.TL_SCHEDULE_1_TRANSPORT.value, ScreenTreasuresLightWard.TL_SCHEDULE_2_TRANSPORT.value]
        name_area_list = [ScreenTreasuresLightWard.TL_SCHEDULE_1_NAME.value, ScreenTreasuresLightWard.TL_SCHEDULE_2_NAME.value]

        self.challenge_schedule = None
        to_challenge_idx: int = -1
        find_schedule: bool = False
        for i in range(2):
            if self.find_area(tp_area_list[i], screen):
                find_schedule = True

                part = cv2_utils.crop_image_only(screen, name_area_list[i].rect)
                schedule_name = self.ctx.ocr.ocr_for_single_line(part)
                existed_schedule = self.run_record.match_existed_schedule(self.schedule_type, schedule_name)
                if existed_schedule is None:
                    self.challenge_schedule = self.run_record.add_schedule(self.schedule_type, schedule_name)
                    to_challenge_idx = i
                elif not existed_schedule['finished']:
                    self.challenge_schedule = existed_schedule
                    to_challenge_idx = i

        if not find_schedule:
            return Operation.round_retry('未检测到相关挑战', wait=1)

        if to_challenge_idx == -1:  # 没有需要挑战的
            return Operation.round_success()

        click_tp = self.ctx.controller.click(tp_area_list[to_challenge_idx].rect.center)
        if click_tp:
            return Operation.round_success(TreasuresLightwardApp.STATUS_SHOULD_CHALLENGE, wait=3)
        else:
            return Operation.round_retry('点击传送失败', wait=1)

    def _check_total_star(self) -> OperationOneRoundResult:
        """
        获取总星数 判断是否需要挑战
        :return:
        """
        op = TlCheckTotalStar(self.ctx, self.schedule_type)
        return Operation.round_by_op(op.execute())

    def _set_schedule_finished(self) -> OperationOneRoundResult:
        """
        设置某一期为挑战完成
        :return:
        """
        self.challenge_schedule['finished'] = True
        self.run_record.save()
        return Operation.round_success()

    def _update_mission_star(self, mission_num: int, star: int):
        log.info('%s 关卡 %d 当前星数 %d', self.challenge_schedule['schedule_name'], mission_num, star)
        self.run_record.update_mission_star(self.challenge_schedule, mission_num, star)

        if self.schedule_type == TreasuresLightwardTypeEnum.FORGOTTEN_HALL and mission_num <= 7:  # 第7关前可以使用最后一关的星数
            for i in range(mission_num):
                previous_mission_star = self.run_record.get_mission_star(self.challenge_schedule, i + 1)
                if previous_mission_star == 0:  # 不可能有0星还能完成后面的
                    self.run_record.update_mission_star(self.challenge_schedule, i + 1, star)

        if mission_num == self._current_mission_num and star == 3:  # 进入下一关
            self._current_mission_num += 1

    def _cal_team_member(self, node_combat_types: List[List[CharacterCombatType]]) -> Optional[List[List[Character]]]:
        """
        根据关卡属性计算对应配队
        :param node_combat_types: 节点对应的属性
        :return:
        """
        module_list = self.config.team_module_list
        filter_module_list = [module for module in module_list if module.fit_schedule_type(self.schedule_type)]
        log.info('开始计算配队 所需属性为 %s', [i.cn for combat_types in node_combat_types for i in combat_types])
        return search_best_mission_team(node_combat_types, filter_module_list)

    def _update_record_after_stop(self, result: OperationResult):
        """
        应用停止后的对运行记录的更新
        :param result: 运行结果
        :return:
        """
        self.run_record.update_status(AppRunRecord.STATUS_SUCCESS)

    def _on_max_unlock_done(self, op_result: OperationResult):
        """
        更新最大的未解锁关卡 忘却之庭部分
        :return:
        """
        if op_result.success:
            max_unlock_num: int = op_result.data
            if max_unlock_num <= 7:
                for i in range(max_unlock_num, 0, -1):  # 7 ~ 1 哪个没3星就从哪个开始
                    if self.run_record.get_mission_star(self.challenge_schedule, i) < 3:
                        self._current_mission_num = i
                        break
            else:  # 已经解锁第7关之后了 哪关没满就打哪
                for i in range(1, max_unlock_num + 1):
                    if self.run_record.get_mission_star(self.challenge_schedule, i) < 3:
                        self._current_mission_num = i
                    break

    def _challenge_next_mission(self) -> OperationOneRoundResult:
        """
        获取下一个挑战关卡的指令
        :return: 指令
        """
        if self.run_record.get_total_star(self.challenge_schedule) == 36:
            return Operation.round_success()

        op = ChallengeForgottenHallMission(self.ctx,
                                           self.schedule_type,
                                           self._current_mission_num, 2,
                                           cal_team_func=self._cal_team_member,
                                           mission_star_callback=self._update_mission_star)
        return Operation.round_by_op(op.execute())

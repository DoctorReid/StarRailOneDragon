from typing import List, Optional

from pydantic import BaseModel

from basic.i18_utils import gt
from basic.log_utils import log
from sr.app import Application, AppRunRecord, AppDescription, register_app
from sr.config import ConfigHolder
from sr.const import phone_menu_const, character_const
from sr.const.character_const import CharacterCombatType
from sr.context import Context
from sr.image.sceenshot import secondary_ui
from sr.operation import Operation, OperationSuccess, OperationFail
from sr.operation.combine import CombineOperation, StatusCombineOperationEdge, StatusCombineOperation
from sr.operation.combine.challenge_forgotten_hall_mission import ChallengeForgottenHallMission
from sr.operation.unit import guide
from sr.operation.unit.forgotten_hall.check_forgotten_hall_star import CheckForgottenHallStar
from sr.operation.unit.guide import survival_index
from sr.operation.unit.guide.choose_guide_tab import ChooseGuideTab
from sr.operation.unit.guide.survival_index import ChooseSurvivalIndexCategory, ChooseSurvivalIndexMission
from sr.operation.unit.menu.click_phone_menu_item import ClickPhoneMenuItem
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu
from sr.operation.unit.wait_in_seconds import WaitInSeconds

FORGOTTEN_HALL = AppDescription(cn='忘却之庭', id='forgotten_hall')
register_app(FORGOTTEN_HALL)


class ForgottenHallRecord(AppRunRecord):

    def __init__(self):
        super().__init__(FORGOTTEN_HALL.id)

    def check_and_update_status(self):
        super().check_and_update_status()
        self.update_status(AppRunRecord.STATUS_WAIT)

    @property
    def star(self) -> int:
        return self.get('star', 0)

    @star.setter
    def star(self, new_value: int):
        self.update('star', new_value)


_forgotten_hall_record: Optional[ForgottenHallRecord] = None


def get_record() -> ForgottenHallRecord:
    global _forgotten_hall_record
    if _forgotten_hall_record is None:
        _forgotten_hall_record = ForgottenHallRecord()
    return _forgotten_hall_record


class ForgottenHallTeam(BaseModel):

    team_name: str
    """配队名称"""

    character_id_list: List[str]
    """配队角色列表"""


class ForgottenHallConfig(ConfigHolder):

    def __init__(self):
        ConfigHolder.__init__(self, FORGOTTEN_HALL.id)

    def _init_after_read_file(self):
        pass

    @property
    def team_list(self) -> List[ForgottenHallTeam]:
        arr = self.get('team_list', [])
        ret = []
        for i in arr:
            ret.append(ForgottenHallTeam.model_validate(i))
        return ret

    @team_list.setter
    def team_list(self, new_list: List[ForgottenHallTeam]):
        dict_arr = []
        for i in new_list:
            dict_arr.append(i.model_dump())
        self.update('team_list', dict_arr)


_forgotten_hall_config: Optional[ForgottenHallConfig] = None


def get_config() -> ForgottenHallConfig:
    global _forgotten_hall_config
    if _forgotten_hall_config is None:
        _forgotten_hall_config = ForgottenHallConfig()
    return _forgotten_hall_config


class ForgottenHallApp(Application):

    def __init__(self, ctx: Context):
        super().__init__(ctx, op_name=gt('忘却之庭 任务', 'ui'),
                         run_record=get_record())

    def _init_before_execute(self):
        record = get_record()
        record.update_status(AppRunRecord.STATUS_RUNNING)

    def _execute_one_round(self) -> int:
        ops: List[Operation] = []
        edges: List[StatusCombineOperationEdge] = []

        op_success = OperationSuccess(self.ctx)  # 操作成功的终点
        ops.append(op_success)

        op1 = OpenPhoneMenu(self.ctx)  # 打开菜单
        op2 = ClickPhoneMenuItem(self.ctx, phone_menu_const.INTERASTRAL_GUIDE)  # 选择【指南】
        ops.append(op1)
        ops.append(op2)
        edges.append(StatusCombineOperationEdge(op_from=op1, op_to=op2))

        op3 = ChooseGuideTab(self.ctx, guide.GUIDE_TAB_3)  # 选择【生存索引】
        ops.append(op3)
        edges.append(StatusCombineOperationEdge(op_from=op2, op_to=op3))

        op4 = ChooseSurvivalIndexCategory(self.ctx, survival_index.CATEGORY_FORGOTTEN_HALL)  # 左边选择忘却之庭
        ops.append(op4)
        edges.append(StatusCombineOperationEdge(op_from=op3, op_to=op4))

        op5 = ChooseSurvivalIndexMission(self.ctx, survival_index.MISSION_FORGOTTEN_HALL)  # 右侧选择忘却之庭传送
        ops.append(op5)
        edges.append(StatusCombineOperationEdge(op_from=op4, op_to=op5))

        op6 = CheckForgottenHallStar(self.ctx, self._update_star)  # 检测星数并更新
        ops.append(op6)
        edges.append(StatusCombineOperationEdge(op_from=op5, op_to=op6))

        edges.append(StatusCombineOperationEdge(op_from=op6, op_to=op_success, status='30'))  # 满星的时候直接设置为成功

        last_mission = OperationSuccess(self.ctx, '3')  # 模拟上个关卡满星
        ops.append(last_mission)
        edges.append(StatusCombineOperationEdge(op_from=op6, op_to=last_mission, ignore_status=True))  # 非满星的时候开始挑战

        for i in range(10):
            mission = ChallengeForgottenHallMission(self.ctx, i + 1, 2,
                                                    self._update_mission_star, self._cal_team_member)
            ops.append(mission)
            edges.append(StatusCombineOperationEdge(op_from=last_mission, op_to=mission, status='3'))  # 只有上一次关卡满星再进入下一个关卡

            edges.append(StatusCombineOperationEdge(op_from=mission, op_to=op_success, ignore_status=True))  # 没满星就不挑战下一个了

            last_mission = mission

        edges.append(StatusCombineOperationEdge(op_from=last_mission, op_to=op_success, ignore_status=True))  # 最后一关无论结果如何都结束

        combine_op: StatusCombineOperation = StatusCombineOperation(self.ctx, ops, edges,
                                                                    op_name=gt('忘却之庭 全流程', 'ui'))

        if combine_op.execute().success:
            return Operation.SUCCESS

        return Operation.FAIL

    def _update_star(self, star: int):
        log.info('忘却之庭 当前总星数 %d', star)
        self.run_record.star = star

    def _update_mission_star(self, mission_num: int, star: int):
        log.info('忘却之庭 关卡 %d 当前星数 %d', mission_num, star)

    def _cal_team_member(self, combat_types_of_session: List[List[CharacterCombatType]]):
        return [
            [character_const.JINGLIU, character_const.PELA, character_const.SILVERWOLF, character_const.FUXUAN],
            [character_const.DANHENGIMBIBITORLUNAE, character_const.TINGYUN, character_const.YUKONG, character_const.LUOCHA],
        ]

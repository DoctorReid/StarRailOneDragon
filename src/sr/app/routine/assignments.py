import time
from typing import Optional

from cv2.typing import MatLike

from basic.i18_utils import gt
from basic.img import MatchResult
from basic.log_utils import log
from sr.app import Application, AppRunRecord, AppDescription, register_app
from sr.const import phone_menu_const
from sr.context import Context
from sr.image.sceenshot import phone_menu
from sr.mystools import mys_config
from sr.operation import Operation
from sr.operation.unit.claim_assignment import ClaimAssignment
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu

ASSIGNMENTS = AppDescription(cn='委托', id='assignments')
register_app(ASSIGNMENTS)


class AssignmentsRecord(AppRunRecord):

    def __init__(self):
        super().__init__(ASSIGNMENTS.id)

    def check_and_update_status(self):
        """
        检查并更新状态 各个app按需实现
        :return:
        """
        if self._should_reset_by_dt() or self.claim_dt < self.get_current_dt():
            self.reset_record()

    def _should_reset_by_dt(self):
        """
        根据米游社便签更新
        有任何一个委托可以接受
        :return:
        """
        if super()._should_reset_by_dt():
            return True
        config = mys_config.get()

        if self.claim_dt >= self.get_current_dt() or self.run_time_float > config.refresh_time:
            return False

        if config.refresh_time > 0:
            now = time.time()
            usage_time = now - config.refresh_time
            e_arr = config.expeditions
            for e in e_arr:
                if e.remaining_time - usage_time <= 0:
                    return True
        return False

    @property
    def claim_dt(self) -> str:
        """
        领取委托奖励的日期
        :return:
        """
        return self.get('claim_dt', '20240101')

    @claim_dt.setter
    def claim_dt(self, new_value: str):
        """
        领取委托奖励的日期
        :return:
        """
        self.update('claim_dt', new_value)


assignments_record: Optional[AssignmentsRecord] = None


def get_record() -> AssignmentsRecord:
    global assignments_record
    if assignments_record is None:
        assignments_record = AssignmentsRecord()
    return assignments_record


class Assignments(Application):

    def __init__(self, ctx: Context):
        super().__init__(ctx, op_name=gt('委托', 'ui'),
                         run_record=get_record())
        self.run_record: AssignmentsRecord = get_record()
        self.phase: int = 0

    def _init_before_execute(self):
        get_record().update_status(AppRunRecord.STATUS_RUNNING)

    def _execute_one_round(self) -> int:
        if self.phase == 0:
            op = OpenPhoneMenu(self.ctx)
            if op.execute().success:
                self.phase += 1
                return Operation.WAIT
            else:
                return Operation.FAIL
        elif self.phase == 1:
            screen: MatLike = self.screenshot()
            result: MatchResult = phone_menu.get_phone_menu_item_pos(screen, self.ctx.im, phone_menu_const.ASSIGNMENTS, alert=True)
            if result is None:
                log.info('检测不到委托红点 跳过')
                return Operation.SUCCESS
            else:
                self.ctx.controller.click(result.center)
                self.phase += 1
                time.sleep(1)
                return Operation.WAIT
        elif self.phase == 2:
            op = ClaimAssignment(self.ctx)
            if op.execute().success:
                self.phase += 1
                self.run_record.claim_dt = self.run_record.get_current_dt()
                return Operation.WAIT
            else:
                return Operation.FAIL
        elif self.phase == 3:  # 领取完返回菜单
            op = OpenPhoneMenu(self.ctx)
            r = op.execute().success
            if not r:
                return Operation.FAIL
            else:
                return Operation.SUCCESS

    @property
    def current_execution_desc(self) -> str:
        """
        当前运行的描述 用于UI展示
        :return:
        """
        return gt('委托', 'ui')

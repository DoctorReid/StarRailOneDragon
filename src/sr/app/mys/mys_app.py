import asyncio

from basic.i18_utils import gt
from basic.log_utils import log
from sr.app.app_run_record import AppRunRecord
from sr.app.application_base import Application2
from sr.context import Context
from sr.operation import Operation, OperationOneRoundResult, StateOperationNode, OperationResult


class MysApp(Application2):

    def __init__(self, ctx: Context):

        game_sign = StateOperationNode('游戏签到', self._game_sign)
        bbs_sign = StateOperationNode('米游币任务', self._bbs_sign)

        super().__init__(ctx,
                         op_name=gt('米游社', 'ui'),
                         nodes=[game_sign, bbs_sign],
                         run_record=ctx.mys_run_record
                         )
        self.game_sign_success: bool = False
        self.bbs_sign_success: bool = False
        self.init_context_before_start = True  # 不需要任何context

    def _game_sign(self) -> OperationOneRoundResult:
        if not self.ctx.mys_config.is_login:
            log.info('未登录米游社账号')
        elif not self.ctx.mys_config.auto_game_sign:
            log.info('未启用自动游戏签到')
        else:
            self.game_sign_success = asyncio.run(self.ctx.mys_config.perform_game_sign())

        return Operation.round_success()

    def _bbs_sign(self) -> OperationOneRoundResult:
        if not self.ctx.mys_config.is_login:
            log.info('未登录米游社账号')
        elif not self.ctx.mys_config.auto_bbs_sign:
            log.info('未启用自动米游币任务')
        else:
            self.bbs_sign_success = asyncio.run(self.ctx.mys_config.perform_bbs_sign())

        return Operation.round_success()

    def _update_record_after_stop(self, result: OperationResult):
        """
        应用停止后的对运行记录的更新
        :param result: 运行结果
        :return:
        """
        if self.run_record is not None:
            if result.success and self.game_sign_success and self.bbs_sign_success:
                self.run_record.update_status(AppRunRecord.STATUS_SUCCESS)
            else:
                self.run_record.update_status(AppRunRecord.STATUS_FAIL)

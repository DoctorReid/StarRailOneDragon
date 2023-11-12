from basic.log_utils import log
from sr.context import Context
from sr.operation import Operation
from sr.operation.unit.enter_game import EnterGame


class Application(Operation):

    def __init__(self, ctx: Context, op_name: str = None,
                 init_context_before_start: bool = True,
                 stop_context_after_stop: bool = True,):
        super().__init__(ctx, op_name=op_name)
        self.init_context_before_start: bool = init_context_before_start
        self.stop_context_after_stop: bool = stop_context_after_stop

    def _init_context(self) -> bool:
        """
        上下文的初始化
        :return: 是否初始化成功
        """
        if not self.init_context_before_start:
            return True

        if not self.ctx.start_running():
            return False

        if self.ctx.open_game_by_script:
            op = EnterGame(self.ctx)
            if not op.execute():
                log.error('进入游戏失败')
                self.ctx.stop_running()
                return False

        return True

    def execute(self) -> bool:
        if not self._init_context():
            return False
        result: bool = super().execute()
        self._stop_context()
        return result

    def on_resume(self):
        super().on_resume()
        self.ctx.controller.init()

    def _stop_context(self):
        if self.stop_context_after_stop:
            self.ctx.stop_running()

    def current_execution_desc(self) -> str:
        """
        当前运行的描述 用于UI展示
        :return:
        """
        return ''

    def next_execution_desc(self) -> str:
        """
        下一步运行的描述 用于UI展示
        :return:
        """
        return ''

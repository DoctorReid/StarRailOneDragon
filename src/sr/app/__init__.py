from basic.log_utils import log
from sr.context import Context
from sr.operation import Operation


class Application(Operation):

    def __init__(self, ctx: Context):
        super().__init__(ctx)

    def execute(self) -> bool:
        if not self.ctx.start_running():
            self.ctx.stop_running()
            return False
        log.info('加载工具中')
        if not self.ctx.init_all(renew=True):
            self.ctx.stop_running()
            return False
        log.info('加载工具完毕')
        self.init_app()
        result: bool = super().execute()
        self.ctx.stop_running()
        return result

    def init_app(self):
        pass

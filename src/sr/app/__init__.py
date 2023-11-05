from basic.log_utils import log
from sr.context import Context
from sr.operation import Operation
from sr.operation.unit.enter_game import EnterGame


class Application(Operation):

    def __init__(self, ctx: Context):
        super().__init__(ctx)

    def execute(self) -> bool:
        if self.ctx.running != 0:
            log.info('请先结束其他运行中的功能 再启动')
            return False
        log.info('加载工具中')
        if not self.ctx.init_all(renew=True):
            self.ctx.stop_running()
            return False
        log.info('加载工具完毕')
        if not self.ctx.start_running():
            self.ctx.stop_running()
            return False
        if self.ctx.open_game_by_script:
            op = EnterGame(self.ctx)
            if not op.execute():
                log.error('进入游戏失败')
                self.ctx.stop_running()
                return False
        self.init_app()
        result: bool = super().execute()
        self.ctx.stop_running()
        return result

    def init_app(self):
        pass

    def on_resume(self):
        super().on_resume()
        self.ctx.controller.init()

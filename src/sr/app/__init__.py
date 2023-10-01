from sr.context import Context


class Application:

    def __init__(self, ctx: Context):
        self.ctx = ctx
        self.ctx.register_pause(self, self.on_pause, self.on_resume)

    def execute(self) -> bool:
        result = self.run()
        self.ctx.unregister(self)
        return result

    def run(self) -> bool:
        pass

    def on_pause(self):
        pass

    def on_resume(self):
        pass

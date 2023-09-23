class Operation:

    def __init__(self):
        pass

    def execute(self, success_callback=None, failure_callback=None) -> bool:
        """执行动作"""
        r = self.inner()
        if r and success_callback is not None:
            success_callback()
        if not r and failure_callback is not None:
            failure_callback()
        return r

    def inner_exe(self) -> bool:
        pass
from concurrent.futures import ThreadPoolExecutor

_debug_executor = None


def get_executor() -> ThreadPoolExecutor:
    global _debug_executor
    if _debug_executor is None:
        _debug_executor = ThreadPoolExecutor(
            thread_name_prefix='debug',
            max_workers=1
        )
    return _debug_executor

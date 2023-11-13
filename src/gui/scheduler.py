import schedule
import time
import threading

from basic.log_utils import log


def start():
    t = threading.Thread(target=_run_schedule)
    t.start()


def every_second(func, seconds: int = 1, tag: str = None):
    s = schedule.every(seconds).seconds.do(func)
    if tag:
        s.tag(tag)


def cancel_with_tag(tag: str):
    schedule.clear(tag)


def _run_schedule():
    while True:
        try:
            schedule.run_pending()
        except Exception:
            log.error('定时任务出错', exc_info=True)
        time.sleep(1)

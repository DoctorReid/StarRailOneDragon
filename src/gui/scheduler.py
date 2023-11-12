import schedule
import time
import threading


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
        schedule.run_pending()
        time.sleep(1)

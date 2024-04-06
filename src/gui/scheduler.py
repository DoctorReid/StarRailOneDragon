from typing import Callable, Optional

import schedule
import time
import threading

from basic.log_utils import log


_is_shutdown: bool = False


def start():
    t = threading.Thread(target=_run_schedule)
    t.start()


def every_second(func, seconds: int = 1, tag: Optional[str] = None):
    s = schedule.every(seconds).seconds.do(func)
    if tag:
        s.tag(tag)


def cancel_with_tag(tag: str):
    schedule.clear(tag)


def with_tag(tag: str) -> bool:
    """
    是否有某个标签的任务
    :param tag:
    :return:
    """
    job_list = schedule.get_jobs(tag)
    return job_list is not None and len(job_list) > 0


def by_hour(hour_num: int, func: Callable, tag: Optional[str] = None):
    """
    按小时启动
    :param hour_num: 小时 0~23
    :param func: 定时执行的任务
    :param tag: 任务标签
    :return:
    """
    s = schedule.every().day.at('%02d:00:01' % hour_num).do(func)  # 加一秒 避免完全整点运行。例如每天4点刷新运行记录 刷新后再运行脚本
    # s = schedule.every().day.at('11:46').do(func)  # 测试代码
    # s = schedule.every().day.at('11:47').do(func)
    if tag is not None:
        s.tag(tag)


def _run_schedule():
    while True:
        if _is_shutdown:
            break
        try:
            schedule.run_pending()
        except Exception:
            log.error('定时任务出错', exc_info=True)
        time.sleep(1)


def shutdown():
    schedule.clear()
    global _is_shutdown
    _is_shutdown = True

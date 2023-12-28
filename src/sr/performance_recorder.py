import time

from basic.log_utils import log


class PerformanceRecord:

    def __init__(self, id: str):
        self.id = id
        self.cnt = 0
        self.total = 0
        self.max = 0
        self.min = 999

    def add(self, t):
        self.cnt += 1
        self.total += t
        if t > self.max:
            self.max = t
        if t < self.min:
            self.min = t

    def avg(self):
        return self.total / self.cnt if self.cnt > 0 else 0

    def __str__(self):
        return ('[%s] 次数: %d 平均耗时: %.6f 最高耗时: %.6f, 最低耗时: %.6f, 总耗时: %.6f' %
                (self.id, self.cnt, self.avg(), self.max, self.min, self.total))


class PerformanceRecorder:

    def __init__(self):
        self.record_map = {}

    def record(self, id: str, t: float):
        """
        记录一个耗时
        :param id:
        :param t:
        :return:
        """
        if id not in self.record_map:
            self.record_map[id] = PerformanceRecord(id)

        self.record_map[id].add(t)

    def get_record(self, id: str):
        return self.record_map[id] if id in self.record_map else PerformanceRecord(id)


recorder = PerformanceRecorder()


def get_recorder():
    return recorder


def add_record(id: str, t: float):
    recorder.record(id, t)


def record_performance(func):
    def wrapper(*args, **kwargs):
        t1 = time.time()
        result = func(*args, **kwargs)
        add_record(func.__name__, time.time() - t1)
        return result
    return wrapper


def get(id: str):
    return recorder.get_record(id)


def log_all_performance():
    log.debug(get('analyse_mini_map'))
    log.debug(get('cal_character_pos_by_sp_result'))
    log.debug(get('cal_character_pos_by_feature_match'))
    log.debug(get('cal_character_pos_by_gray'))
    log.debug(get('cal_character_pos_by_road_mask'))
    log.debug(get('cal_character_pos_by_original'))
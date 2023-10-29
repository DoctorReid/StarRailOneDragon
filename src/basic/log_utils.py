import logging
import os
from logging.handlers import TimedRotatingFileHandler

from basic import os_utils


def get_logger():
    logger = logging.getLogger('StarRailAutoProxy')
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG if os_utils.is_debug() else logging.INFO)

    formatter = logging.Formatter('[%(asctime)s] [%(funcName)s %(lineno)d] [%(levelname)s]: %(message)s', '%H:%M:%S')

    log_file_path = os.path.join(os_utils.get_path_under_work_dir('.log'), 'log.txt')
    archive_handler = TimedRotatingFileHandler(log_file_path, when='midnight', interval=1, backupCount=3)
    archive_handler.setLevel(logging.DEBUG if os_utils.is_debug() else logging.INFO)  # 文件输出默认debug
    archive_handler.setFormatter(formatter)
    logger.addHandler(archive_handler)

    # console_handler = logging.StreamHandler()
    # console_handler.setLevel(logging.DEBUG if os_utils.is_debug() else logging.INFO)  # 前台日志默认info
    # console_handler.setFormatter(formatter)
    # logger.addHandler(console_handler)

    return logger


log = get_logger()

if __name__ == '__main__':
    log.info('test')

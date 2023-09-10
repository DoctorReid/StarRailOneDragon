import logging
import os
from logging.handlers import TimedRotatingFileHandler

from platform import os_utils


def get_logger():
    logger = logging.getLogger('Star Rail Copilot')
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('[%(asctime)s] [%(funcName)s] [%(levelname)s]: %(message)s')

    log_file_path = os.path.join(os_utils.get_path_under_work_dir('.log'), 'log.txt')
    archive_handler = TimedRotatingFileHandler(log_file_path, when='midnight', interval=1, backupCount=3)
    archive_handler.setLevel(logging.DEBUG)  # 文件输出默认debug
    archive_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if os_utils.is_debug() else logging.INFO)  # 前台日志默认info
    console_handler.setFormatter(formatter)

    logger.addHandler(archive_handler)
    logger.addHandler(console_handler)

    return logger


log = get_logger()

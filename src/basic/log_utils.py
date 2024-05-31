import logging
import os
from logging.handlers import TimedRotatingFileHandler

from basic import os_utils


def get_logger():
    logger = logging.getLogger('StarRailOneDragon')
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG if os_utils.is_debug() else logging.INFO)

    formatter = logging.Formatter('[%(asctime)s.%(msecs)03d] [%(filename)s %(lineno)d] [%(levelname)s]: %(message)s', '%H:%M:%S')

    log_file_path = os.path.join(os_utils.get_path_under_work_dir('.log'), 'log.txt')
    archive_handler = TimedRotatingFileHandler(log_file_path, when='midnight', interval=1, backupCount=3, encoding='utf-8')
    archive_handler.setLevel(logging.DEBUG if os_utils.is_debug() else logging.INFO)
    archive_handler.setFormatter(formatter)
    logger.addHandler(archive_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if os_utils.is_debug() else logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


log = get_logger()

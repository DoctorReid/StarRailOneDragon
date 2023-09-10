import gettext

from platform import os_utils
from platform.log_utils import log


def get_i18_func():
    translate_path = os_utils.get_path_under_work_dir('data', 'locales')
    log.debug('多语言文件位置 %s' % translate_path)
    gettext.bindtextdomain('src', translate_path)
    translation = gettext.translation('src', localedir=translate_path, languages=['cn'])
    # 注册翻译函数为全局函数
    translation.install()
    return translation.gettext


gt = get_i18_func()

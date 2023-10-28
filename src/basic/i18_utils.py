import gettext

from basic import os_utils

_gt = {}
_default_lang = 'cn'


def get_translations(model: str, lang: str):
    """
    加载语音
    :param model: 模块 将ocr 界面 日志等翻译区分开来
    :param lang: 语言
    :return:
    """
    translate_path = os_utils.get_path_under_work_dir('data', 'locales')
    gettext.bindtextdomain(model, translate_path)
    translation = gettext.translation(model, localedir=translate_path, languages=[lang])
    # 注册翻译函数为全局函数
    translation.install()
    return translation


def gt(msg: str, model: str = 'ocr', lang: str = None):
    if lang is None:
        lang = _default_lang
    if model not in _gt:
        _gt[model] = {}
    if lang not in _gt[model]:
        _gt[model][lang] = get_translations(model, lang)
    return _gt[model][lang].gettext(msg)


def update_default_lang(lang: str):
    global _default_lang
    _default_lang = lang


def get_default_lang() -> str:
    """
    获取默认语言
    :return:
    """
    global _default_lang
    return _default_lang

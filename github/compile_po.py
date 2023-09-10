import polib
import os

from platform import os_utils


def compile_lang(lang: str):
    """
    将特定语言的文件编译成mo文件
    :param lang: 语言 cn
    :return: None
    """
    po_file_path = os.path.join(os_utils.get_path_under_work_dir('data', 'locales', 'origin'), '%s.po' % lang)
    mo_file_path = os.path.join(os_utils.get_path_under_work_dir('data', 'locales', lang, 'LC_MESSAGES'), 'src.mo')

    po = polib.pofile(po_file_path)
    po.save_as_mofile(mo_file_path)


def compile_po_files():
    """
    将不同语言的po文件编译成mo
    :return:
    """
    compile_lang('cn')

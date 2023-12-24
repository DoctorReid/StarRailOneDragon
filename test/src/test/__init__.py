import os
from typing import List

from cv2.typing import MatLike

from basic import os_utils
from basic.img import cv2_utils


class SrTestBase:

    resources_sub_dirs: List[str]
    """测试资源所在目录"""

    def __init__(self, file):
        os.environ['DEBUG'] = '1'

        # 获取本基类的路径
        base_file_path = os.path.abspath(__file__)
        # 获取本基类所在的包路径
        base_package_path: str = os.path.dirname(base_file_path)

        # 获取子类的路径
        sub_file_path = os.path.abspath(file)
        # 获取子类所在的包路径
        sub_package_path: str = os.path.dirname(sub_file_path)

        self.resources_sub_dirs: List[str] = ['test', 'resources']

        for sub in sub_package_path[len(base_package_path) + 1:].split('\\'):
            self.resources_sub_dirs.append(sub)
        self.resources_sub_dirs.append(os.path.basename(sub_file_path)[:-3])

    def _get_test_image(self, file_name: str, suffix: str = '.png') -> MatLike:
        """
        获取测试图片
        :param file_name: 文件名
        :param suffix: 后缀
        :return:
        """
        img_path = self._get_test_image_path(file_name, suffix)
        return cv2_utils.read_image(img_path)

    def _get_test_image_path(self, file_name: str, suffix: str = '.png') -> str:
        """
        获取测试图片的路径
        :param file_name: 文件名
        :param suffix: 后缀
        :return:
        """
        dir_path = os_utils.get_path_under_work_dir(*self.resources_sub_dirs)
        return os.path.join(dir_path, '%s%s' % (file_name, suffix))

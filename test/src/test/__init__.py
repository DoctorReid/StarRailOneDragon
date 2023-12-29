import os
from typing import List, Optional

import cv2
from cv2.typing import MatLike

from basic import os_utils, Rect
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

    def get_test_image(self, file_name: str, suffix: str = '.png') -> MatLike:
        """
        获取测试图片
        :param file_name: 文件名
        :param suffix: 后缀
        :return:
        """
        img_path = self.get_test_image_path(file_name, suffix)
        return cv2_utils.read_image(img_path)

    def get_test_image_path(self, file_name: str, suffix: str = '.png') -> str:
        """
        获取测试图片的路径
        :param file_name: 文件名
        :param suffix: 后缀
        :return:
        """
        dir_path = os_utils.get_path_under_work_dir(*self.resources_sub_dirs)
        return os.path.join(dir_path, '%s%s' % (file_name, suffix))

    def black_part(self, img: MatLike, rect: Rect, save: Optional[str] = None, show: bool = True):
        """
        将某部分涂黑 用于遮挡敏感信息
        :param img: 图片
        :param rect: 区域
        :param save: 保存的文件名 为空时不保存
        :param show: 是否显示
        :return:
        """
        img2 = cv2.rectangle(img, (rect.x1, rect.y1), (rect.x2, rect.y2), (0, 0, 0), -1)
        if show:
            cv2_utils.show_image(img2, win_name='black_part', wait=0)
        if save is not None:
            file_path = self.get_test_image_path(save)
            cv2.imwrite(file_path, img2)
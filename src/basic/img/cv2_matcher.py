import time
from typing import Union

import cv2
import os

from basic import os_utils
from basic.img import ImageMatcher, ImageLike, MatchResultList, cv2_utils
from basic.log_utils import log


class CvImageMatcher(ImageMatcher):

    def __init__(self, x_scale: float = 1, y_scale: float = 1):
        self.templates = {}
        self.x_scale = x_scale
        self.y_scale = y_scale
        template_folder = os_utils.get_path_under_work_dir('images', 'template')
        for filename in os.listdir(template_folder):
            file_path = os.path.join(template_folder, filename)
            if not os.path.isfile(file_path) or not filename.endswith('.png'):
                continue
            self.load_template(filename[:-4], file_path)

        need_360 = ['loc_arrow']
        for i in need_360:
            if i not in self.templates:
                continue
            template = self.templates[i]
            for angle in range(360):
                rotate_id = '%s_%d' % (i, angle)
                rotate_template = cv2_utils.image_rotate(template, angle)
                self.templates[rotate_id] = rotate_template

    def load_template(self, template_id: str, template_path: str):
        """
        加载需要匹配的模板到内存中 后续使用模板id匹配即可
        :param template_id: 模板id
        :param template_path: 模板路径
        :param x_scale: 读取后缩放比例x
        :param y_scale: 读取后缩放比例y
        :return:
        """
        res = cv2_utils.read_image_with_alpha(template_path)
        if self.x_scale != 1 or self.y_scale != 1:
            res = cv2.resize(res, (0, 0), fx=self.x_scale, fy=self.y_scale)

        self.templates[template_id] = res

    def get_template(self, template: ImageLike):
        """
        获取对应模板图片
        :param template: 模板id 或 模板图片
        :return: 模板图片
        """
        if type(template) == str:
            if template not in self.templates:
                return None
            return self.templates[template]
        else:
            return template

    def match_template(self, source: ImageLike, template: str, threshold: float = 0.5,
                       src_x_scale: float = 1, src_y_scale: float = 1,
                       ignore_template_alpha: bool = False,
                       ignore_inf: bool = True, show_result: bool = False) -> MatchResultList:
        """
        在原图中 匹配模板
        :param source: 原图
        :param template: 模板
        :param threshold: 匹配阈值
        :param src_x_scale: 原图缩放比例x
        :param src_y_scale: 原图缩放比例y
        :param ignore_inf: 是否忽略无限大的结果
        :param show_result：是否在最后显示结果图片
        :return: 所有匹配结果
        """
        template: cv2.typing.MatLike = self.get_template(template)
        if template is None:
            log.error('未加载模板 %s' % template)
            return MatchResultList()
        match_result_list = cv2_utils.match_template(source, template, threshold,
                                                     ignore_template_alpha=ignore_template_alpha,
                                                     ignore_inf=ignore_inf)

        log.debug('模板[%s]匹配结果 %s', template if type(template) == str else '', str(match_result_list))

        if show_result and len(match_result_list) > 0:
            for i in match_result_list:
                cv2.rectangle(source, (i.x, i.y), (i.x + i.w, i.y + i.h), (255, 0, 0), 1)
            cv2.imshow('Result', source)
        return match_result_list

    def get_rotate_template(self, template: Union[str, cv2.typing.MatLike], angle: int):
        """
        获取旋转后的模板
        :param template: 模板图片、模板id
        :param angle: 角度
        :return:
        """
        if type(template) == str:
            rotate_id = '%s_%d' % (template, angle)
            if rotate_id in self.templates:
                return self.templates[rotate_id]
            else:
                return cv2_utils.image_rotate(self.templates[template], angle)
        else:
            return cv2_utils.image_rotate(template, angle)

    def match_template_with_rotation(self, source: ImageLike, template: str, threshold: float = 0.5,
                                     ignore_inf: bool = True, show_result: bool = False) -> dict:
        """
        在原图中 对模板进行360度旋转匹配。方法耗时较长 注意原图尽量小一点
        :param source: 原图
        :param template: 模板
        :param threshold: 匹配阈值
        :param ignore_inf: 是否忽略无限大的结果
        :param show_result：是否在最后显示结果图片
        :return: 每个选择角度的匹配结果
        """
        source: cv2.typing.MatLike = cv2_utils.convert_source(source)

        angle_result = {}
        for i in range(360):
            rt = self.get_rotate_template(template, i)
            result: MatchResultList = cv2_utils.match_template(source, rt, threshold,
                                                               ignore_template_alpha=True,
                                                               ignore_inf=ignore_inf)
            if len(result) > 0:
                angle_result[i] = result

        return angle_result


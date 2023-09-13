from typing import Union, List

import cv2.typing
from PIL.Image import Image

ImageLike = Union[Image, cv2.typing.MatLike, str]


class MatchResult:

    def __init__(self, c, x, y, w, h):
        self.confidence = c
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def __str__(self):
        return '({%.2f}, {%d}, {%d})' % (self.confidence, self.x, self.y)


class MatchResultList:

    def __init__(self):
        self.arr: List[MatchResult] = []

    def __str__(self):
        return '[%s]' % ', '.join(str(i) for i in self.arr)

    def __iter__(self):
        self.index = 0
        return self

    def __next__(self):
        if self.index < len(self.arr):
            value = self.arr[self.index]
            self.index += 1
            return value
        else:
            raise StopIteration

    def append(self, a: MatchResult, auto_merge: bool = True, merge_distance: float = 10):
        """
        添加匹配结果，如果开启合并，则保留置信度更高的结果
        :param a: 需要添加的结构
        :param auto_merge: 是否与之前结果进行合并
        :param merge_distance: 多少距离内的
        :return:
        """
        if auto_merge:
            for i in self.arr:
                if (i.x - a.x) ** 2 + (i.y - a.y) ** 2 <= merge_distance ** 2:
                    if a.confidence > i.confidence:
                        i.x = a.x
                        i.y = a.y
                        i.confidence = a.confidence
                    return

        self.arr.append(a)


class ImageMatcher:

    def load_template(self, template_id: str, template_path: str, x_scale: float = 1, y_scale: float = 1):
        """
        加载需要匹配的模板到内存中 后续使用模板id匹配即可
        :param template_id: 模板id
        :param template_path: 模板路径
        :param x_scale: 读取后缩放比例x
        :param y_scale: 读取后缩放比例y
        :return:
        """
        pass

    def match_template_by_id(self, source_image: ImageLike, template_id: str, threshold: float = 0,
                             src_x_scale: float = 1, src_y_scale: float = 1,
                             show_result: bool = False) -> MatchResultList:
        """
        在原图中 匹配模板
        :param source_image: 原图
        :param template_id: 模板id
        :param threshold: 匹配阈值
        :param src_x_scale: 原图缩放比例x
        :param src_y_scale: 原图缩放比例y
        :param show_result：是否在最后显示结果图片
        :return: 所有匹配结果
        """
        pass

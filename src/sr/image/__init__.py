from typing import Union, List

import cv2
import numpy as np

from basic.img import MatchResultList


class ImageMatcher:

    def match_template(self, source: cv2.typing.MatLike, template: Union[cv2.typing.MatLike, str],
                       threshold: float = 0.5, ignore_inf: bool = True,
                       ignore_template_alpha: bool = True,
                       mask: np.ndarray = None,
                       show: bool = False) -> MatchResultList:
        """
        在原图中 匹配模板
        :param source: 原图
        :param template: 模板图片 或 模板id
        :param threshold: 匹配阈值
        :param ignore_inf: 是否忽略无限大的结果
        :param ignore_template_alpha: 是否忽略模板中的透明通道。会与掩码合并
        :param mask: 掩码
        :param show：是否显示匹配结果
        :return: 所有匹配结果
        """
        pass

    def match_template_with_rotation(self, source: cv2.typing.MatLike, template: Union[str, cv2.typing.MatLike],
                                     threshold: float = 0.5, ignore_inf: bool = True,
                                     ignore_template_alpha: bool = True,
                                     mask: np.ndarray = None,
                                     show: bool = False) -> dict:
        """
        在原图中 对模板进行360度旋转匹配
        :param source: 原图
        :param template: 模板图片 或 模板id
        :param threshold: 匹配阈值
        :param ignore_template_alpha: 是否忽略模板中的透明通道。会与掩码合并
        :param mask: 掩码
        :param ignore_inf: 是否忽略无限大的结果
        :param show：是否在最后显示结果图片
        :return: 每个选择角度的匹配结果
        """
        pass


class OcrMatcher:

    def run_ocr(self, image: cv2.typing.MatLike, threshold: float = 0.5) -> dict:
        """
        对图片进行OCR 返回所有匹配结果
        :param image: 图片
        :param threshold: 匹配阈值
        :return: {key_word: []}
        """
        pass

    def match_words(self, image: cv2.typing.MatLike, words: List[str], threshold: float = 0.5) -> dict:
        """
        在图片中查找关键词 返回所有词对应的位置
        :param image: 图片
        :param words: 关键词
        :param threshold: 匹配阈值
        :return: {key_word: []}
        """
        all_match_result: dict = self.run_ocr(image, threshold)
        match_key = set()
        for k in all_match_result.keys():
            for w in words:
                if k.find(w) != -1:
                    match_key.add(k)
                    break

        return {key: all_match_result[key] for key in match_key if key in all_match_result}

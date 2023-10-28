from typing import List

from cv2.typing import MatLike

from basic.i18_utils import gt


class OcrMatcher:

    def ocr_for_single_line(self, image: MatLike, threshold: float = None, strict_one_line: bool = True) -> str:
        """
        识别单行文本
        :param image: 图片
        :param threshold: 阈值
        :param strict_one_line: 是否严格单行 非严格情况下会
        :return:
        """
        pass

    def run_ocr(self, image: MatLike, threshold: float = None) -> dict:
        """
        对图片进行OCR 返回所有匹配结果
        :param image: 图片
        :param threshold: 匹配阈值
        :return: {key_word: []}
        """
        pass

    def match_words(self, image: MatLike, words: List[str], threshold: float = None, same_word: bool = False) -> dict:
        """
        在图片中查找关键词 返回所有词对应的位置
        :param image: 图片
        :param words: 关键词
        :param threshold: 匹配阈值
        :param same_word: 要求整个词一样
        :return: {key_word: []}
        """
        all_match_result: dict = self.run_ocr(image, threshold)
        match_key = set()
        for k in all_match_result.keys():
            for w in words:
                ocr_world = gt(w, 'ocr')
                if same_word and k == ocr_world:
                    match_key.add(k)
                elif not same_word and k.find(ocr_world) != -1:
                    match_key.add(k)
                    break

        return {key: all_match_result[key] for key in match_key if key in all_match_result}



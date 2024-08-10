from typing import List, Optional

from cv2.typing import MatLike

from basic import str_utils, Rect
from basic.i18_utils import gt
from basic.img import MatchResult, MatchResultList, cv2_utils


class OcrMatcher:

    def run_ocr_single_line(self, image: MatLike, threshold: float = None, strict_one_line: bool = True) -> str:
        """
        识别单行文本
        :param image: 图片
        :param threshold: 阈值
        :param strict_one_line: True时认为当前只有单行文本 False时依赖程序合并成一行
        :return:
        """
        pass

    def run_ocr(self, image: MatLike, threshold: float = None, merge_line_distance: float = -1) -> dict[str, MatchResultList]:
        """
        对图片进行OCR 返回所有匹配结果
        :param image: 图片
        :param threshold: 匹配阈值
        :param merge_line_distance: 多少行距内合并结果 -1为不合并
        :return: {key_word: []}
        """
        pass

    def match_words(self, image: MatLike, words: List[str], threshold: float = None,
                    same_word: bool = False,
                    ignore_case: bool = True, lcs_percent: float = -1, merge_line_distance: float = -1) -> dict[str, MatchResultList]:
        """
        在图片中查找关键词 返回所有词对应的位置
        :param image: 图片
        :param words: 关键词
        :param threshold: 匹配阈值
        :param same_word: 要求整个词一样
        :param ignore_case: 忽略大小写
        :param lcs_percent: 最长公共子序列长度百分比 -1代表不使用 same_word=True时不生效
        :param merge_line_distance: 多少行距内合并结果 -1为不合并
        :return: {key_word: []}
        """
        all_match_result: dict = self.run_ocr(image, threshold, merge_line_distance=merge_line_distance)
        match_key = set()
        for k in all_match_result.keys():
            for w in words:
                ocr_result: str = k
                ocr_target = gt(w, 'ocr')
                if ignore_case:
                    ocr_result = ocr_result.lower()
                    ocr_target = ocr_target.lower()

                if same_word:
                    if ocr_result == ocr_target:
                        match_key.add(k)
                else:
                    if lcs_percent == -1:
                        if ocr_result.find(ocr_target) != -1:
                            match_key.add(k)
                    else:
                        if str_utils.find_by_lcs(ocr_target, ocr_result, percent=lcs_percent):
                            match_key.add(k)

        return {key: all_match_result[key] for key in match_key if key in all_match_result}

    def match_one_best_word(self, image: MatLike, word: str, lcs_percent: Optional[float] = None) -> Optional[MatchResult]:
        """
        匹配一个文本 只返回一个最佳的结果
        适合在目标文本只会出现一次的场景下使用
        :param image: 图片
        :param word: 关键词
        :param lcs_percent: 所需的最低LCS阈值
        :return:
        """
        ocr_map = self.run_ocr(image)

        target_result: Optional[MatchResult] = None
        target_lcs_percent: Optional[float] = None

        word_to_find = gt(word, 'ocr')

        for word, match_result_list in ocr_map.items():
            current_lcs = str_utils.longest_common_subsequence_length(word_to_find, word)
            current_lcs_percent = current_lcs / len(word_to_find)

            if lcs_percent is not None and current_lcs_percent < lcs_percent:  # 不满足最低阈值
                continue

            if target_result is None or target_lcs_percent is None or target_lcs_percent < current_lcs_percent:
                target_result = match_result_list.max
                target_lcs_percent = current_lcs_percent

        return target_result

    def match_word_in_one_line(self, image: MatLike, word: str,
                               threshold: float = None, strict_one_line: bool = True,
                               lcs_percent: Optional[float] = 1,
                               part_rect: Optional[Rect] = None) -> bool:
        """
        应该在只有单行文本的图片中使用
        判断图中的文本是否是目标文本
        :param image: 图片
        :param word: 目标文本
        :param threshold: OCR识别的阈值
        :param strict_one_line: True时认为当前只有单行文本 False时依赖程序合并成一行
        :param lcs_percent: 需要满足的最长公共子序列长度百分比
        :param part_rect: 扫描部分截图
        :return:
        """
        img_to_ocr = image if part_rect is None else cv2_utils.crop_image(image, part_rect)[0]
        ocr_result = self.run_ocr_single_line(img_to_ocr, threshold=threshold, strict_one_line=strict_one_line)
        return str_utils.find_by_lcs(gt(word, 'ocr'), ocr_result, percent=lcs_percent)
    
    def run_ocr_without_det(self, image: MatLike, threshold: float = None) -> str:
        """
        单文字OCR
        :param image: 图片
        :param threshold: 匹配阈值
        :return: [("text", "score"),]
        """
        pass

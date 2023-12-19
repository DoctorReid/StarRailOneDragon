from typing import List

from cv2.typing import MatLike

from basic import str_utils
from basic.i18_utils import gt
from basic.img import MatchResult, MatchResultList


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
    
    def run_ocr_without_det(self, image: MatLike, threshold: float = None) -> str:
        """
        单文字OCR
        :param image: 图片
        :param threshold: 匹配阈值
        :return: [("text", "score"),]
        """
        pass


def merge_ocr_result_to_single_line(ocr_map, join_space: bool = True) -> str:
    """
    将OCR结果合并成一行 用于过长的文体产生换行
    :param ocr_map: run_ocr的结果
    :param join_space: 连接时是否加入空格
    :return:
    """
    lines: List[List[MatchResult]] = []
    for text, result_list in ocr_map.items():
        for result in result_list:
            in_line: int = -1
            for line_idx in range(len(lines)):
                for line_item in lines[line_idx]:
                    if abs(line_item.center.y - result.center.y) <= 5:
                        in_line = line_idx
                        break
                if in_line != -1:
                    break

            if in_line == -1:
                lines.append([result])
            else:
                lines[in_line].append(result)

    result_str: str = None
    for line in lines:
        sorted_line = sorted(line, key=lambda x: x.center.x)
        for result_item in sorted_line:
            if result_str is None:
                result_str = result_item.data
            else:
                result_str += (' ' if join_space else '') + result_item.data

    return result_str


def merge_ocr_result_to_multiple_line(ocr_map, join_space: bool = True, merge_line_distance: float = 40) -> dict[str, MatchResultList]:
    """
    将OCR结果合并成多行 用于过长的文体产生换行
    :param ocr_map: run_ocr的结果
    :param join_space: 连接时是否加入空格
    :param merge_line_distance: 多少行距内合并结果
    :return:
    """
    lines = []
    for text, result_list in ocr_map.items():
        for result in result_list:
            in_line: int = -1
            for line_idx in range(len(lines)):
                for line_item in lines[line_idx]:
                    if abs(line_item.center.y - result.center.y) <= merge_line_distance:
                        in_line = line_idx
                        break
                if in_line != -1:
                    break

            if in_line == -1:
                lines.append([result])
            else:
                lines[in_line].append(result)

    merge_ocr_result_map: dict[str, MatchResultList] = {}
    for line in lines:
        line_ocr_map = {}
        merge_result: MatchResult = MatchResult(1, 9999, 9999, 0, 0)
        for ocr_result in line:
            if ocr_result.data not in line_ocr_map:
                line_ocr_map[ocr_result.data] = MatchResultList()
            line_ocr_map[ocr_result.data].append(ocr_result)

            if ocr_result.x < merge_result.x:
                merge_result.x = ocr_result.x
            if ocr_result.y < merge_result.y:
                merge_result.y = ocr_result.y
            if ocr_result.x + ocr_result.w > merge_result.x + merge_result.w:
                merge_result.w = ocr_result.x + ocr_result.w - merge_result.x
            if ocr_result.y + ocr_result.h > merge_result.y + merge_result.h:
                merge_result.h = ocr_result.y + ocr_result.h - merge_result.y

        merge_result.data = merge_ocr_result_to_single_line(line_ocr_map, join_space=join_space)
        if merge_result.data not in merge_ocr_result_map:
            merge_ocr_result_map[merge_result.data] = MatchResultList()
        merge_ocr_result_map[merge_result.data].append(merge_result)

    return merge_ocr_result_map

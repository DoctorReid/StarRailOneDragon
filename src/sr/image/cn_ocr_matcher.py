import logging

from cnocr import CnOcr
from cv2.typing import MatLike

from basic import os_utils
from basic.i18_utils import gt
from basic.img import MatchResultList, MatchResult
from basic.log_utils import log
from sr.image.ocr_matcher import OcrMatcher, merge_ocr_result_to_single_line


logging.getLogger().handlers.clear()  # 不知道为什么 CnOcr模块会引入这个logger 清除掉避免console中有重复日志


class CnOcrMatcher(OcrMatcher):
    """
    https://cnocr.readthedocs.io/zh/latest/
    """
    def __init__(self):
        self.ocr: CnOcr = None
        try:
            self.ocr = CnOcr(det_model_name='ch_PP-OCRv2_det',
                             rec_model_name='densenet_lite_136-fc',
                             det_root=os_utils.get_path_under_work_dir('model', 'cnocr'),
                             rec_root=os_utils.get_path_under_work_dir('model', 'cnstd'))
        except Exception:
            log.error(gt('OCR模型加载出错'), exc_info=True)

    def ocr_for_single_line(self, image: MatLike, threshold: float = None, strict_one_line: bool = True) -> str:
        """
        单行文本识别 手动合成一行 按匹配结果从左到右 从上到下
        理论中文情况不会出现过长分行的 这里只是为了兼容英语的情况
        :param image: 图片
        :param threshold: 阈值
        :param strict_one_line: 严格判断只有单行文本 False时合并成一行
        :return:
        """
        if strict_one_line:
            result = self.ocr.ocr_for_single_line(image)
            log.debug('OCR结果 %s', result['text'])
            return result['text'] if threshold is None or result['score'] >= threshold else None
        else:
            ocr_map: dict = self.run_ocr(image, threshold)
            return merge_ocr_result_to_single_line(ocr_map, join_space=False)

    def run_ocr(self, image: MatLike, threshold: float = None,
                merge_line_distance: float = -1) -> dict:
        """
        对图片进行OCR 返回所有匹配结果
        :param image: 图片
        :param threshold: 匹配阈值
        :param merge_line_distance: 多少行距内合并结果 -1为不合并 理论中文情况不会出现过长分行的 这里只是为了兼容英语的情况
        :return: {key_word: []}
        """
        scan_result: list = self.ocr.ocr(image)
        result_map: dict = {}
        for r in scan_result:
            if threshold is not None and r['score'] < threshold:
                continue
            if r['text'] not in result_map:
                result_map[r['text']] = MatchResultList()
            result_map[r['text']].append(MatchResult(r['score'],
                                                     r['position'][0][0],
                                                     r['position'][0][1],
                                                     r['position'][2][0] - r['position'][0][0],
                                                     r['position'][2][1] - r['position'][0][1],
                                                     data=r['text']))
        log.debug('OCR结果 %s', result_map.keys())
        return result_map

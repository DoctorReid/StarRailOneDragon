from cnocr import CnOcr
from cv2.typing import MatLike

from basic import os_utils
from basic.img import MatchResultList, MatchResult
from basic.log_utils import log
from sr.image.ocr_matcher import OcrMatcher


class EnOcrMatcher(OcrMatcher):
    """
    https://cnocr.readthedocs.io/zh/latest/
    """

    def __init__(self):
        self.ocr: CnOcr = None
        try:
            self.ocr = CnOcr(det_model_name='en_PP-OCRv3_det',
                             rec_model_name='densenet_lite_136-fc',
                             det_root=os_utils.get_path_under_work_dir('model', 'cnocr'),
                             rec_root=os_utils.get_path_under_work_dir('model', 'cnstd'))
        except Exception:
            log.error('OCR模型加载出错', exc_info=True)

    def ocr_for_single_line(self, image: MatLike, threshold: float = None, lang: str = None,
                            strict_one_line: bool = True) -> str:
        """
        Some
        :param image:
        :param threshold:
        :param lang:
        :return:
        """
        result = self.ocr.ocr_for_single_line(image)
        log.debug('OCR结果 %s', result.keys())
        return result['text'] if threshold is None or result['score'] >= threshold else None

    def run_ocr(self, image: MatLike, threshold: float = None, lang: str = None) -> dict:
        """
        对图片进行OCR 返回所有匹配结果
        :param image: 图片
        :param threshold: 匹配阈值
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
                                                     r['position'][2][1] - r['position'][0][1]))
        log.debug('OCR结果 %s', result_map.keys())
        return result_map
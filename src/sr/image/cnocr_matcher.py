from cnocr import CnOcr
from cv2.typing import MatLike

from basic import os_utils
from basic.img import MatchResultList, MatchResult
from basic.log_utils import log
from sr.image import OcrMatcher


class CnOcrMatcher(OcrMatcher):
    """
    https://cnocr.readthedocs.io/zh/latest/
    """

    def __init__(self,
                 det_model_name: str = 'ch_PP-OCRv2_det',  # 实测这个比 ch_PP-OCRv3_det 更适合
                 rec_model_name: str = 'densenet_lite_136-fc'):  # densenet_lite_136-gru
        try:
            self.ocr = CnOcr(det_model_name=det_model_name,
                             rec_model_name=rec_model_name,
                             det_root=os_utils.get_path_under_work_dir('model', 'cnocr'),
                             rec_root=os_utils.get_path_under_work_dir('model', 'cnstd'))
        except Exception:
            log.error('OCR模型加载出错', exc_info=True)

    def ocr_for_single_line(self, image: MatLike, threshold: float = 0.5) -> str:
        result = self.ocr.ocr_for_single_line(image)
        log.debug('OCR结果 %s', result)
        if result['score'] > threshold:
            return result['text']

    def run_ocr(self, image: MatLike, threshold: float = 0.5) -> dict:
        """
        对图片进行OCR 返回所有匹配结果
        :param image: 图片
        :param threshold: 匹配阈值
        :return: {key_word: []}
        """
        scan_result: list = self.ocr.ocr(image)
        result_map: dict = {}
        for r in scan_result:
            if r['score'] < threshold:
                continue
            if r['text'] not in result_map:
                result_map[r['text']] = MatchResultList()
            result_map[r['text']].append(MatchResult(r['score'],
                                                     r['position'][0][0],
                                                     r['position'][0][1],
                                                     r['position'][2][0] - r['position'][0][0],
                                                     r['position'][2][1] - r['position'][0][1]))
        log.debug('OCR结果 %s', result_map)
        return result_map

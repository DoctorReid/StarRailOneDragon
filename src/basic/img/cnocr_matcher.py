from cnocr import CnOcr

from basic import os_utils
from basic.img import OcrMatcher, ImageLike, MatchResultList, MatchResult


class CnocrMatcher(OcrMatcher):
    """
    https://cnocr.readthedocs.io/zh/latest/
    """

    def __init__(self,
                 det_model_name: str = 'ch_PP-OCRv2_det',
                 rec_model_name: str = 'densenet_lite_136-fc'):
        self.ocr = CnOcr(det_model_name=det_model_name,
                         rec_model_name=rec_model_name,
                         det_root=os_utils.get_path_under_work_dir('model', 'cnocr'),
                         rec_root=os_utils.get_path_under_work_dir('model', 'cnstd'))

    def run_ocr(self, image: ImageLike, threshold: float = 0.5) -> dict:
        """
        对图片进行OCR 返回所有匹配结果
        :param image: 图片
        :param threshold: 匹配阈值
        :return: {key_word: []}
        """
        scan_result: list = self.ocr.ocr(image)
        result_map: dict = {}
        for r in scan_result:
            print(r)
            if r['score'] < threshold:
                continue
            if r['text'] not in result_map:
                result_map[r['text']] = MatchResultList()
            result_map[r['text']].append(MatchResult(r['score'],
                                                     r['position'][0][0],
                                                     r['position'][0][1],
                                                     r['position'][2][0] - r['position'][0][0],
                                                     r['position'][2][1] - r['position'][0][1]))
        return result_map

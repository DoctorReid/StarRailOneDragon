import logging
from typing import Optional

from cv2.typing import MatLike
from paddleocr import PaddleOCR

from basic import os_utils
from basic.img import MatchResultList, MatchResult
from basic.log_utils import log
from sr.image.ocr_matcher import OcrMatcher, merge_ocr_result_to_single_line

logging.getLogger().handlers.clear()  # 不知道为什么 这里会引入这个logger 清除掉避免console中有重复日志


class EnOcrMatcher(OcrMatcher):
    """
    https://github.com/PaddlePaddle/PaddleOCR/blob/release/2.7/doc/doc_ch/quickstart.md
    ocr.ocr(img) 返回的是一个list, for example:
    [
        [ [[894.0, 252.0], [1024.0, 252.0], [1024.0, 288.0], [894.0, 288.0]], ('快速恢复', 0.9989572763442993)],
        [ [[450.0, 494.0], [560.0, 494.0], [560.0, 530.0], [450.0, 530.0]], ('奇巧零食', 0.9995825290679932)]
    ]
    返回锚框的坐标是[[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
    """
    def __init__(self):
        self.ocr: Optional[PaddleOCR] = None
        try:
            # 不使用方向检测, CPU推理, drop_score控制识别模型的精度,模型默认0.5 (rec)
            # 不启用空格识别 (rec) 文字空间结构交给 det 处理
            self.ocr = PaddleOCR(use_angle_cls=False, lang="ch", use_gpu=False, use_space_char=True, drop_score=0.5,  # 传入ch也能识别英文
                                 det_model_dir=os_utils.get_path_under_work_dir('model', 'ch_PP-OCRv4_det_infer'),
                                 rec_model_dir=os_utils.get_path_under_work_dir('model', 'ch_PP-OCRv4_rec_infer'),
                                 cls_model_dir=os_utils.get_path_under_work_dir('model', 'ch_ppocr_mobile_v2.0_cls_infer')
                                 )
        except Exception:
            log.error('OCR模型加载出错', exc_info=True)

    def ocr_for_single_line(self, image: MatLike, threshold: float = None, strict_one_line: bool = True) -> str:
        """
        单行文本识别 部分英语很长 会分成两行 手动合成一行 按匹配结果从左到右 从上到下
        :param image: 图片
        :param threshold: 阈值
        :param strict_one_line: True时认为当前只有单行文本 False时依赖程序合并成一行
        :return:
        """
        if strict_one_line:
            return self.run_ocr_without_det(image, threshold)
        else:
            ocr_map: dict = self.run_ocr(image, threshold)
            tmp = merge_ocr_result_to_single_line(ocr_map, join_space=True)
            log.debug('OCR结果 %s', tmp)
            return tmp

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
        for anchor in scan_result:
            anchor_position = anchor[0]
            anchor_text = anchor[1][0]
            anchor_score = anchor[1][1]
            if threshold is not None and anchor_score < threshold:
                continue
            if anchor_text not in result_map:
                result_map[anchor_text] = MatchResultList(only_best=False)
            result_map[anchor_text].append(MatchResult(anchor_score,
                                                       anchor_position[0][0],
                                                       anchor_position[0][1],
                                                       anchor_position[1][0] - anchor_position[0][0],
                                                       anchor_position[3][1] - anchor_position[0][1],
                                                       data=anchor_text))
        log.debug('OCR结果 %s', result_map.keys())
        return result_map

    def run_ocr_without_det(self, image: MatLike, threshold: float = None) -> str:
        """
        不使用检测模型分析图片内文字的分布
        默认传入的图片仅有文字信息
        :param image: 图片
        :param threshold: 匹配阈值
        :return: [("text", "score"),] 由于禁用了空格，可以直接取第一个元素
        """
        scan_result: list = self.ocr.ocr(image, det=False, cls=False)
        if len(scan_result) > 1:
            log.debug("禁检测的OCR模型返回多个识别结果")  # 目前没有出现这种情况

        if threshold is not None and scan_result[0][1] < threshold:
            log.debug("OCR模型返回的识别结果置信度低于阈值")
            return ""
        log.debug('OCR结果 %s', scan_result)
        return scan_result[0][0]
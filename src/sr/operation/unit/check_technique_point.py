import time
from typing import ClassVar, Optional

from cv2.typing import MatLike

from basic import Rect, str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.context import Context
from sr.image.ocr_matcher import OcrMatcher
from sr.image.sceenshot import battle
from sr.operation import Operation, OperationOneRoundResult


class CheckTechniquePoint(Operation):

    POINT_RECT: ClassVar[Rect] = Rect(1654, 836, 1673, 862)

    def __init__(self, ctx: Context):
        """
        需在大世界页面中使用
        通过右下角数字 检测当前剩余的秘技点数
        返回附加状态为秘技点数
        :param ctx:
        """
        super().__init__(ctx, try_times=5, op_name=gt('检测秘技点数', 'ui'))

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()
        if battle.IN_WORLD != battle.get_battle_status(screen, self.ctx.im):
            time.sleep(1)
            return Operation.round_retry('未在大世界界面')

        digit = CheckTechniquePoint.get_technique_point(screen, self.ctx.ocr)

        if digit is None:
            return Operation.round_retry('未检测到数字', wait=0.5)

        return Operation.round_success(status=str(digit), data=digit)

    @staticmethod
    def get_technique_point(screen: MatLike,
                            ocr: OcrMatcher) -> Optional[int]:
        part, _ = cv2_utils.crop_image(screen, CheckTechniquePoint.POINT_RECT)

        ocr_result = ocr.ocr_for_single_line(part, strict_one_line=True)
        return str_utils.get_positive_digits(ocr_result, None)

from typing import ClassVar, Optional, Callable

from cv2.typing import MatLike

from basic import Rect, str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.context import Context
from sr.operation import Operation, OperationOneRoundResult


class GetTrainingScore(Operation):

    SCORE_RECT: ClassVar[Rect] = Rect(320, 345, 370, 370)

    def __init__(self, ctx: Context, score_callback: Optional[Callable] = None):
        """
        需要在【指南】-【每日实训】页面中使用
        获取当前实训点数
        :param ctx: 上下文
        :param score_callback: 获取分数后的回调
        """
        super().__init__(
            ctx,
            op_name='%s %s' % (
                gt('每日实训', 'ui'),
                gt('识别活跃度', 'ui')
            )
        )
        self.score_callback: Optional[Callable] = score_callback

    def _execute_one_round(self) -> OperationOneRoundResult:
        score = self._get_score()

        if score is None:
            return Operation.round_retry('识别不到数字')
        else:
            if self.score_callback is not None:
                self.score_callback(score)
            return Operation.round_success(str(score))

    def _get_score(self, screen: Optional[MatLike] = None) -> Optional[int]:
        """
        获取当前实训点数
        :param screen: 屏幕截图
        :return: 实训点数
        """
        if screen is None:
            screen = self.screenshot()

        part, _ = cv2_utils.crop_image(screen, GetTrainingScore.SCORE_RECT)
        ocr_result = self.ctx.ocr.ocr_for_single_line(part)

        for i in range(1, 6):  # 优先判断1-5数字是否有出现
            if ocr_result.find(str(i)) != -1:
                return i * 100

        if str_utils.get_positive_digits(ocr_result, None) is None:
            return None
        else:
            return 0  # 有数字又没有1-5的情况 按0返回

from typing import ClassVar, Optional

from cv2.typing import MatLike

from basic import Point, Rect, str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.context import Context
from sr.image.sceenshot.screen_state import in_secondary_ui, ScreenState
from sr.operation import Operation, OperationOneRoundResult


class ChooseSimUniNum(Operation):

    CURRENT_NUM_RECT: ClassVar[Rect] = Rect(0, 0, 0, 0)  # 当前宇宙文本的位置
    PREVIOUS_BTN: ClassVar[Point] = Point(0, 0)  # 点一个换到上一个宇宙
    NEXT_BTN: ClassVar[Point] = Point(0, 0)  # 点一个换到下一个宇宙
    NUM_CN: ClassVar[dict[int, str]] = {
        1: '一',
        2: '二',
        3: '三',
        4: '四',
        5: '五',
        6: '六',
        7: '七',
        8: '八',
    }

    def __init__(self, ctx: Context, num: int):
        """
        需要在模拟宇宙入口页面中使用 且先选择了普通模拟宇宙
        选择对应的宇宙
        :param ctx:
        :param num: 第几宇宙 支持 1~8
        """
        super().__init__(ctx, try_times=5,
                         op_name='%s %s %d' % (gt('模拟宇宙', 'ui'), gt('选择宇宙', 'ui'), num))

        self.num: int = num

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen: MatLike = self.screenshot()

        if not in_secondary_ui(screen, self.ctx.ocr, ScreenState.SIM_TYPE_NORMAL.value):
            return Operation.round_retry('未在模拟宇宙页面', wait=1)

        current_num = self._get_current_num(screen)

        if current_num is None:
            return Operation.round_retry('未识别到模拟宇宙数字', wait=1)
        elif current_num == self.num:
            self.ctx.controller.click(ChooseSimUniNum.CURRENT_NUM_RECT.center)
            return Operation.round_success()
        elif current_num > self.num:
            self.ctx.controller.click(ChooseSimUniNum.PREVIOUS_BTN)
            return Operation.round_retry('未选择目标宇宙', wait=1)
        else:
            self.ctx.controller.click(ChooseSimUniNum.NEXT_BTN)
            return Operation.round_retry('未选择目标宇宙', wait=1)

    def _get_current_num(self, screen: Optional[MatLike]) -> Optional[int]:
        """
        获取当前选择了哪个宇宙
        :param screen: 屏幕截图
        :return:
        """
        if screen is None:
            screen = self.screenshot()

        part, _ = cv2_utils.crop_image(screen)

        ocr_result = self.ctx.ocr.ocr_for_single_line(part)

        for num, word in ChooseSimUniNum.NUM_CN.items():
            if str_utils.find_by_lcs(gt(word, 'ocr'), ocr_result, percent=1):
                return num

        return None


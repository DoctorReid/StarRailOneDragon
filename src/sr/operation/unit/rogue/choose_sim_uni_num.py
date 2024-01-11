from typing import ClassVar, Optional

from cv2.typing import MatLike

from basic import Point, Rect, str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.context import Context
from sr.image.sceenshot.screen_state import in_secondary_ui, ScreenState
from sr.operation import Operation, OperationOneRoundResult
from sr.const.rogue_const import UNI_NUM_CN


class ChooseSimUniNum(Operation):

    CURRENT_NUM_RECT: ClassVar[Rect] = Rect(805, 515, 945, 552)  # 当前宇宙文本的位置
    GOING_RECT: ClassVar[Rect] = Rect(813, 484, 888, 511)  # 进行中

    CURRENT_BTN: ClassVar[Point] = Point(1276, 567)  # 选择当前宇宙
    PREVIOUS_BTN: ClassVar[Point] = Point(1216, 198)  # 换到上一个宇宙
    NEXT_BTN: ClassVar[Point] = Point(1173, 929)  # 换到下一个宇宙

    def __init__(self, ctx: Context, num: int):
        """
        需要在模拟宇宙入口页面中使用 且先选择了普通模拟宇宙
        选择对应的宇宙 如果有进行中的宇宙 会先继续完成
        :param ctx:
        :param num: 第几宇宙 支持 1~8
        """
        super().__init__(ctx,
                         try_times=5,
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
            self.ctx.controller.click(ChooseSimUniNum.CURRENT_BTN)
            return Operation.round_success(wait=2, data=self.num)
        else:
            if self._is_going(screen):
                self.ctx.controller.click(ChooseSimUniNum.CURRENT_BTN)
                return Operation.round_success(wait=2, data=current_num)

            if current_num > self.num:
                self.ctx.controller.click(ChooseSimUniNum.PREVIOUS_BTN)
                return Operation.round_retry('未选择目标宇宙', wait=2)
            else:
                self.ctx.controller.click(ChooseSimUniNum.NEXT_BTN)
                return Operation.round_retry('未选择目标宇宙', wait=2)

    def _get_current_num(self, screen: Optional[MatLike]) -> Optional[int]:
        """
        获取当前选择了哪个宇宙
        :param screen: 屏幕截图
        :return:
        """
        if screen is None:
            screen = self.screenshot()

        part, _ = cv2_utils.crop_image(screen, ChooseSimUniNum.CURRENT_NUM_RECT)

        ocr_result = self.ctx.ocr.ocr_for_single_line(part)

        for num, word in UNI_NUM_CN.items():
            if str_utils.find_by_lcs(gt(word, 'ocr'), ocr_result, percent=1):
                return num

        return None

    def _is_going(self, screen: Optional[MatLike] = None) -> bool:
        """
        当前宇宙是否进行中
        :param screen: 屏幕截图
        :return:
        """
        if screen is None:
            screen = self.screenshot()

        return self.ctx.ocr.match_word_in_one_line(screen, '进行中',
                                                   part_rect=ChooseSimUniNum.GOING_RECT,
                                                   lcs_percent=0.1
                                                   )


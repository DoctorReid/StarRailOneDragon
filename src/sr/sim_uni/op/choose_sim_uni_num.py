from typing import ClassVar, Optional, Callable

from cv2.typing import MatLike

from basic import Point, str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.context.context import Context
from sr.image.sceenshot import screen_state
from sr.image.sceenshot.screen_state import in_secondary_ui
from sr.image.sceenshot.screen_state_enum import ScreenState
from sr.operation import Operation, OperationOneRoundResult, OperationResult
from sr.screen_area.screen_sim_uni import ScreenSimUni
from sr.sim_uni.sim_uni_const import UNI_NUM_CN


class ChooseSimUniNum(Operation):

    CURRENT_BTN: ClassVar[Point] = Point(1276, 567)  # 选择当前宇宙
    PREVIOUS_BTN: ClassVar[Point] = Point(1216, 198)  # 换到上一个宇宙
    NEXT_BTN: ClassVar[Point] = Point(1173, 929)  # 换到下一个宇宙

    STATUS_RESTART: ClassVar[str] = '重新开始'
    STATUS_CONTINUE: ClassVar[str] = '继续'

    def __init__(self, ctx: Context, num: int,
                 op_callback: Optional[Callable[[OperationResult], None]] = None):
        """
        需要在模拟宇宙入口页面中使用 且先选择了普通模拟宇宙
        选择对应的宇宙 如果有进行中的宇宙 会先继续完成
        返回结果中的 data 为实际挑战的第几宇宙
        :param ctx:
        :param num: 第几宇宙 支持 1~8
        """
        super().__init__(ctx,
                         try_times=10,
                         op_name='%s %s %d' % (gt('模拟宇宙', 'ui'), gt('选择宇宙', 'ui'), num),
                         op_callback=op_callback)

        self.num: int = num

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen: MatLike = self.screenshot()

        if not in_secondary_ui(screen, self.ctx.ocr, ScreenState.SIM_TYPE_NORMAL.value):
            # 有可能出现了每周第一次打开的积分奖励进度画面 随便点击一个地方关闭
            self.ctx.controller.click(screen_state.TargetRect.UI_TITLE.value.center)
            return self.round_retry('未在模拟宇宙页面', wait=1)

        current_num = self._get_current_num(screen)

        if current_num is None:
            return self.round_retry('未识别到模拟宇宙数字', wait=1)
        elif current_num == self.num:
            self.ctx.controller.click(ChooseSimUniNum.CURRENT_BTN)
            return self.round_success(status=ChooseSimUniNum.STATUS_RESTART, wait=2, data=self.num)
        else:
            if self._is_going(screen):
                self.ctx.controller.click(ChooseSimUniNum.CURRENT_BTN)
                return self.round_success(status=ChooseSimUniNum.STATUS_CONTINUE, wait=2, data=current_num)

            if current_num > self.num:
                self.ctx.controller.click(ChooseSimUniNum.PREVIOUS_BTN)
                return self.round_retry('未选择目标宇宙', wait=2)
            else:
                self.ctx.controller.click(ChooseSimUniNum.NEXT_BTN)
                return self.round_retry('未选择目标宇宙', wait=2)

    def _get_current_num(self, screen: Optional[MatLike]) -> Optional[int]:
        """
        获取当前选择了哪个宇宙
        :param screen: 屏幕截图
        :return:
        """
        if screen is None:
            screen = self.screenshot()

        area_list = [ScreenSimUni.CURRENT_NUM_1.value, ScreenSimUni.CURRENT_NUM_2.value]
        for area in area_list:
            part = cv2_utils.crop_image_only(screen, area.rect)
            # cv2_utils.show_image(part, win_name='choose_sim_uni_num', wait=0)

            ocr_result = self.ctx.ocr.ocr_for_single_line(part)

            for num, word in UNI_NUM_CN.items():
                if str_utils.find_by_lcs(gt('第%s世界' % word, 'ocr'), ocr_result, percent=1):
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

        area_list = [ScreenSimUni.GOING_1.value, ScreenSimUni.GOING_2.value]
        for area in area_list:
            if self.find_area(area, screen):
                return True
        return False

from typing import ClassVar
import numpy as np
import time
from cv2.typing import MatLike

from basic import Point, Rect
from basic.img import cv2_utils
from basic.log_utils import log

from sr.operation import Operation, OperationOneRoundResult
from sr.control import GameController


class UseRecipe(Operation):
    """
    使用秘技
    """
    QUICK_RECOVERY: ClassVar[Rect] = Rect(870, 236, 1048, 300)  # 秘技点耗光之后按 E 弹出的窗口中的文本位置 "快速恢复"
    ACK_BUTTON: ClassVar[Point] = Point(1168, 818)  # 确认按钮
    CEL_BUTTON: ClassVar[Point] = Point(746, 818)  # 取消按钮
    # ROW_GAP = 113  # 一行两个道具之间的像素差
    # COL_GAP = 148  # 一列两个道具之间的像素差
    
    RECIPE_POS_DICT: dict[str:Point] = {
        '1-1': Point(975, 383),
        '1-2': Point(1108, 383),
        '1-3': Point(1241, 383),
        '1-4': Point(1374, 383),
        '2-1': Point(975, 531),
        '2-2': Point(1108, 531),
        '2-3': Point(1241, 531),
        '2-4': Point(1374, 531)
        }
    
    def __init__(self, ctx):
        self.recipe_status = 0  # 秘技点剩余数量
        super().__init__(ctx, op_name='使用秘技')

    def _execute_one_round(self) -> OperationOneRoundResult:
        ctrl: GameController = self.ctx.controller
        ctrl.use_technique()
        time.sleep(0.5)  # 稍微等待一下, 不然截图可能截不全

        if self._check_recipe_out_of_use(): # 秘技点耗光
            # 点击奇巧零食的位置
            # todo: 用目标检测 识别奇巧零食的位置
            ctrl.click(UseRecipe.RECIPE_POS_DICT["2-3"])
            time.sleep(0.5)

            # 使用两次秘技点后退出
            ctrl.click(UseRecipe.ACK_BUTTON)
            time.sleep(0.5)
            ctrl.click(UseRecipe.ACK_BUTTON)
            time.sleep(0.5)
            ctrl.click(UseRecipe.CEL_BUTTON)
            time.sleep(0.5)
            self.recipe_status = 4  # 一般来说都是消耗"奇巧零食"来补充秘技点的,不适配其他道具了

            ctrl.use_technique()
            self.recipe_status -= 1
            return Operation.SUCCESS
        
        # OCR识别可能出错, 如果在弹出窗口后没识别出有窗口，会一直卡住
        # 保底点击一下取消按钮的位置
        ctrl.click(UseRecipe.CEL_BUTTON)
        return Operation.SUCCESS
    
    def _check_recipe_out_of_use(self):
        """
        判断秘技点是否已经耗光
        """
        if self.recipe_status > 0:
            return False
        else:
            screen = self.screenshot()

            part, _ = cv2_utils.crop_image(screen, UseRecipe.QUICK_RECOVERY)

            ocr_result = self.ctx.ocr.match_words(part, words=["快速恢复"], threshold=0.5)
            if len(ocr_result) > 0:
                log.debug("快速恢复匹配成功")
                return True
            else:
                log.debug("当前秘技点不需要补充")
                return False
from typing import Optional, Callable

from cv2.typing import MatLike, Rect, Point

from basic.i18_utils import gt
from basic.img import MatchResult, cv2_utils
from sr.context import Context
from sr.image.sceenshot import secondary_ui
from sr.operation import Operation, OperationOneRoundResult, OperationResult
from sr.operation.unit.forgotten_hall import get_all_mission_num_pos


class CheckMaxUnlockMission(Operation):

    def __init__(self, ctx: Context, op_callback: Optional[Callable[[OperationResult], None]] = None):
        """
        需要在忘却之庭页面中使用
        找到最大的已经解锁的关卡 正常情况进入忘却之庭首页就是显示这个
        返回状态为关卡数字
        :param ctx: 应用上下文
        :param op_callback: 指令回调
        """
        super().__init__(ctx, try_times=5,
                         op_name='%s %s' % (gt('忘却之庭', 'ui'), gt('最大解锁关卡', 'ui')),
                         op_callback=op_callback
                         )

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        if not secondary_ui.in_secondary_ui(screen, self.ctx.ocr, secondary_ui.SecondaryUiTitle.TITLE_FORGOTTEN_HALL.value):
            return Operation.round_retry('未进入 ' + secondary_ui.SecondaryUiTitle.TITLE_FORGOTTEN_HALL.value, 1)

        max_unlock_num = self.get_max_unlock_num(screen)

        if max_unlock_num is None:
            return Operation.round_retry('未找到已解锁关卡')
        else:
            return Operation.round_success()

    def get_max_unlock_num(self, screen: Optional[MatLike]) -> Optional[int]:
        """
        找到
        :param screen:
        :return:
        """
        if screen is None:
            screen = self.screenshot()
        num_pos_map = get_all_mission_num_pos(self.ctx, screen)

        i = 13
        while True:
            i -= 1
            if i == 0:
                break
            if i not in num_pos_map:  # 目前图片没有这个关卡
                continue

            if self.is_lock_under_nun(screen, num_pos_map[i]):
                continue

            return i

        return None

    def is_lock_under_nun(self, screen: MatLike, num_pos: MatchResult) -> bool:
        """
        判断该位置下方是否有 未解锁 的字
        :param screen: 屏幕截图
        :param num_pos: 关卡号码的位置
        :return:
        """
        lt = num_pos.center + Point(-100, 20)
        rb = num_pos.center + Point(100, 50)
        rect = Rect(lt.x, lt.y, rb.x, rb.y)

        part, _ = cv2_utils.crop_image(screen, rect)

        return self.ctx.ocr.match_word_in_one_line(part, '未解锁', strict_one_line=True, lcs_percent=0.1)

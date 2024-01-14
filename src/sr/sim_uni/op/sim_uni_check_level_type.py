from typing import Optional, Callable

from basic import str_utils
from basic.i18_utils import gt
from sr.context import Context
from sr.image.sceenshot import screen_state
from sr.operation import Operation, OperationOneRoundResult, OperationResult
from sr.sim_uni.sim_uni_const import SimUniLevelTypeEnum


class SimUniCheckLevelType(Operation):

    def __init__(self, ctx: Context,
                 op_callback: Optional[Callable[[OperationResult], None]] = None):
        """
        模拟宇宙中使用 识别当前楼层类型
        需要先保证在大世界画面
        """
        super().__init__(ctx, try_times=5,
                         op_name='%s %s' % (gt('模拟宇宙', 'ui'), gt('识别楼层类型', 'ui')),
                         op_callback=op_callback
                         )

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        if not screen_state.is_normal_in_world(screen, self.ctx.im):
            return Operation.round_retry('未在大世界画面', wait=1)

        region_name = screen_state.get_region_name(screen, self.ctx.ocr)
        level_type_list = [enum.value for enum in SimUniLevelTypeEnum]
        target_list = [gt(level_type.type_name, 'ocr') for level_type in level_type_list]
        target_idx = str_utils.find_best_match_by_lcs(region_name, target_list)

        if target_idx is not None:
            level_type = level_type_list[target_idx]
            return Operation.round_success(status=level_type.type_id, data=level_type)
        else:
            return Operation.round_retry('识别区域类型失败', wait=1)

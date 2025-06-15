from typing import Optional, ClassVar

from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils import cv2_utils, str_utils
from one_dragon.utils.i18_utils import gt
from sr_od.app.div_uni.div_uni_const import DivUniLevelType
from sr_od.app.div_uni.operations.div_uni_choose_curio import DivUniChooseCurio
from sr_od.app.div_uni.operations.div_uni_click_empty_after_interact import DivUniClickEmptyAfterInteract
from sr_od.app.div_uni.operations.div_uni_run_level_combat import DivUniRunLevelCombat
from sr_od.context.sr_context import SrContext
from sr_od.operations.sr_operation import SrOperation
from cv2.typing import MatLike


class DivUniRunLevel(SrOperation):

    STATUS_NEXT_ENTRY: ClassVar[str] = '可进入下层'

    def __init__(self, ctx: SrContext, assume_level_type: DivUniLevelType = DivUniLevelType.COMBAT):
        """
        选择存档 最终返回【位面饰品提取】画面
        """
        SrOperation.__init__(self, ctx, op_name=gt('差分宇宙-层间移动', 'ui'))

        self.assume_level_type: DivUniLevelType = assume_level_type  # 由调用方传入 预估的楼层类型
        self.confirm_level_type: Optional[DivUniLevelType] = None  # 有画面识别 确认的楼层类型

    @node_from(from_name='处理需交互界面', status='差分宇宙-大世界')  # 处理后返回画面继续
    @operation_node(name='识别初始画面', is_start_node=True)
    def check_initial_screen(self) -> OperationRoundResult:
        screen = self.screenshot()
        current_screen_name: str = self.check_screen_name(screen)

        if current_screen_name is None:
            return self.round_retry(status='未能识别当前画面', wait=1)
        else:
            return self.round_success(status=current_screen_name)

    def check_screen_name(self, screen: MatLike) -> str:
        return self.check_and_update_current_screen(
            screen,
            [
                '差分宇宙-大世界',

                '模拟宇宙-获得物品',
                '模拟宇宙-获得奇物',
                '模拟宇宙-获得祝福',
                '差分宇宙-获得方程',

                '差分宇宙-选择奇物',
                '差分宇宙-选择祝福',
            ]
        )

    @node_from(from_name='识别初始画面', status='差分宇宙-大世界')
    @operation_node(name='处理大世界画面')
    def handle_normal_world(self) -> OperationRoundResult:
        screen = self.screenshot()
        if self.confirm_level_type is None:
            self.confirm_level_type = self.get_level_type(screen)

        op: Optional[SrOperation] = None
        level_type = self.confirm_level_type if self.confirm_level_type is not None else self.assume_level_type
        if level_type == DivUniLevelType.COMBAT:
            op = DivUniRunLevelCombat(self.ctx)

        if op is not None:
            op_result = op.execute()
            if op_result.success:
                return self.round_success(status=DivUniRunLevel.STATUS_NEXT_ENTRY)
            else:
                return self.round_retry(status=op_result.status, wait=1)

        return self.round_retry(status='未识别当前区域', wait=1)

    def get_level_type(self, screen: MatLike) -> Optional[DivUniLevelType]:
        """
        识别当前画面的楼层类型
        """
        level_type_list: list[DivUniLevelType] = [i for i in DivUniLevelType]
        target_word_list: list[str] = [gt(i.value) for i in level_type_list]

        area = self.ctx.screen_loader.get_area('差分宇宙-大世界', '标题-区域类型')
        part = cv2_utils.crop_image_only(screen, area.rect)
        ocr_result_map = self.ctx.ocr.run_ocr(part)

        for ocr_result in ocr_result_map.keys():
            for target_idx, target_word in enumerate(target_word_list):
                if ocr_result.find(target_word) >= 0:
                    return level_type_list[target_idx]

        return None

    @node_from(from_name='识别初始画面', status='模拟宇宙-获得物品')
    @node_from(from_name='识别初始画面', status='模拟宇宙-获得奇物')
    @node_from(from_name='识别初始画面', status='模拟宇宙-获得祝福')
    @node_from(from_name='识别初始画面', status='差分宇宙-获得方程')
    @node_from(from_name='识别初始画面', status='差分宇宙-选择奇物')
    @node_from(from_name='识别初始画面', status='差分宇宙-选择祝福')
    @operation_node(name='处理需交互画面')
    def handle_interact_screen(self) -> OperationRoundResult:
        screen = self.screenshot()

        op: Optional[SrOperation] = None
        current_screen_name: str = self.check_screen_name(screen)
        if current_screen_name is None:
            return self.round_retry(status='当前画面无需交互', wait=1)
        elif current_screen_name in ['模拟宇宙-获得物品', '模拟宇宙-获得奇物', '差分宇宙-获得方程', '模拟宇宙-获得祝福',]:
            op = DivUniClickEmptyAfterInteract(self.ctx, skip_initial_screen_check=True)
        elif current_screen_name == '差分宇宙-选择奇物':
            op = DivUniChooseCurio(self.ctx, skip_initial_screen_check=True)
        elif current_screen_name == '差分宇宙-选择祝福':
            op = DivUniChooseCurio(self.ctx, skip_initial_screen_check=True)
        elif current_screen_name == '差分宇宙-大世界':
            return self.round_success(current_screen_name)

        if op is not None:
            op_result = op.execute()
            if op_result.success:
                return self.round_wait(status=op_result.status)
            else:
                return self.round_retry(status=op_result.status, wait=1)

        return self.round_success(status='处理完成')


    @node_from(from_name='处理大世界画面', status=STATUS_NEXT_ENTRY)
    @operation_node(name='处理下层入口')
    def handle_next_entry(self) -> OperationRoundResult:
        pass

def __debug():
    ctx = SrContext()
    ctx.ocr.init_model()
    ctx.init_by_config()
    ctx.div_uni_context.init_for_div_uni()
    ctx.start_running()

    op = DivUniRunLevel(ctx)
    op.execute()


if __name__ == '__main__':
    __debug()
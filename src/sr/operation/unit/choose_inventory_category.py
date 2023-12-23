import time

from basic import Point
from basic.i18_utils import gt
from sr.context import Context
from sr.image.sceenshot import secondary_ui
from sr.operation import Operation, OperationOneRoundResult


class InventoryCategory:
    def __init__(self, template_id: str, cn: str, pos: Point):
        """背包类目"""

        self.template_id: str = template_id
        """模板ID"""
        self.cn: str = cn
        """类目名称"""
        self.pos: Point = pos
        """位置"""


INVENTORY_CATEGORY_UPGRADE_MATERIALS = InventoryCategory(template_id='upgrade_materials', cn='养成材料', pos=Point(636, 60))
INVENTORY_CATEGORY_LIGHT_CONE = InventoryCategory(template_id='light_cone', cn='光锥', pos=Point(725, 60))
INVENTORY_CATEGORY_RELICS = InventoryCategory(template_id='relics', cn='遗器', pos=Point(835, 60))
INVENTORY_CATEGORY_OTHER_MATERIALS = InventoryCategory(template_id='other_materials', cn='其它材料', pos=Point(920, 60))
INVENTORY_CATEGORY_CONSUMABLES = InventoryCategory(template_id='consumables', cn='消耗品', pos=Point(1025, 60))
INVENTORY_CATEGORY_MISSIONS = InventoryCategory(template_id='missions', cn='任务', pos=Point(1125, 60))
INVENTORY_CATEGORY_VALUABLES = InventoryCategory(template_id='valuables', cn='贵重品', pos=Point(1215, 60))


class ChooseInventoryCategory(Operation):

    def __init__(self, ctx: Context, category: InventoryCategory):
        """
        需要在【背包】页面使用
        点击对应类目
        :param ctx:
        :param category:
        """
        super().__init__(ctx, try_times=5,
                         op_name='%s %s' % (gt('背包 选择类目', 'ui'), gt(category.cn, 'ui')))

        self.category: InventoryCategory = category

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()
        if not secondary_ui.in_secondary_ui(screen, self.ctx.ocr, title_cn=secondary_ui.TITLE_INVENTORY.cn):
            time.sleep(1)
            return Operation.round_retry('未在背包页面')

        if not secondary_ui.in_secondary_ui(screen, self.ctx.ocr, title_cn=self.category.cn):
            click = self.ctx.controller.click(self.category.pos)
            time.sleep(1)
            if click:
                return Operation.round_wait()
            else:
                return Operation.round_retry('%s %s' % ('点击分类失败', self.category.cn))

        return Operation.round_success()

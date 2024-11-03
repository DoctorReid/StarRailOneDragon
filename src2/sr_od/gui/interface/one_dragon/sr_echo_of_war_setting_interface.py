from PySide6.QtWidgets import QWidget
from typing import List

from one_dragon.gui.component.column_widget import ColumnWidget
from one_dragon.gui.component.interface.vertical_scroll_interface import VerticalScrollInterface
from sr_od.app.trailblaze_power.trailblaze_power_config import TrailblazePowerPlanItem
from sr_od.context.sr_context import SrContext
from sr_od.gui.interface.one_dragon.sr_power_plan_interface import PowerPlanCard


class EchoOfWarSettingInterface(VerticalScrollInterface):

    def __init__(self, ctx: SrContext, parent=None):
        self.ctx: SrContext = ctx

        VerticalScrollInterface.__init__(
            self,
            object_name='sr_echo_of_war_setting_interface',
            content_widget=None, parent=parent,
            nav_text_cn='历战回响'
        )

    def get_content_widget(self) -> QWidget:
        self.content_widget = ColumnWidget()

        self.card_list: List[PowerPlanCard] = []

        self.content_widget.add_stretch(1)
        return self.content_widget

    def on_interface_shown(self) -> None:
        VerticalScrollInterface.on_interface_shown(self)

        self.update_plan_list_display()

    def update_plan_list_display(self):
        plan_list = self.ctx.echo_of_war_config.plan_list

        if len(plan_list) > len(self.card_list):

            while len(self.card_list) < len(plan_list):
                idx = len(self.card_list)
                card = PowerPlanCard(self.ctx, idx, plan_list[idx])
                card.changed.connect(self.on_plan_item_changed)

                self.card_list.append(card)
                self.content_widget.add_widget(card)

        for idx, plan in enumerate(plan_list):
            card = self.card_list[idx]
            card.init_with_plan(plan)

        while len(self.card_list) > len(plan_list):
            card = self.card_list[-1]
            self.content_widget.remove_widget(card)
            card.deleteLater()
            self.card_list.pop(-1)

        for card in self.card_list:
            card.category_combo_box.setVisible(False)
            card.mission_combo_box.setDisabled(True)
            card.del_btn.setVisible(False)
            card.move_up_btn.setVisible(False)

    def on_plan_item_changed(self, idx: int, plan: TrailblazePowerPlanItem) -> None:
        self.ctx.echo_of_war_config.update_plan(idx, plan)

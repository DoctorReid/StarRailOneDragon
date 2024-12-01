from PySide6.QtWidgets import QWidget
from qfluentwidgets import SettingCardGroup, FluentIcon

from one_dragon.gui.widgets.setting_card.combo_box_setting_card import ComboBoxSettingCard
from one_dragon.gui.widgets.setting_card.switch_setting_card import SwitchSettingCard
from one_dragon.gui.widgets.vertical_scroll_interface import VerticalScrollInterface
from one_dragon.utils.i18_utils import gt
from phosdeiz.gui.widgets import Column
from sr_od.app.relic_salvage.relic_salvage_config import RelicLevelEnum
from sr_od.context.sr_context import SrContext


class SrOdSettingInterface(VerticalScrollInterface):

    def __init__(self, ctx: SrContext, parent=None):
        self.ctx: SrContext = ctx

        VerticalScrollInterface.__init__(
            self,
            object_name='sr_od_setting_interface',
            content_widget=None, parent=parent,
            nav_text_cn='其他设置'
        )

    def get_content_widget(self) -> QWidget:
        content_widget = Column()

        content_widget.add_widget(self.get_relic_salvage_group())
        content_widget.add_stretch(1)

        return content_widget

    def get_relic_salvage_group(self) -> QWidget:
        group = SettingCardGroup(gt('遗器分解'))

        self.relic_salvage_level_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='遗器分解等级',
                                                           options_enum=RelicLevelEnum)
        group.addSettingCard(self.relic_salvage_level_opt)

        self.relic_salvage_abandon_opt = SwitchSettingCard(icon=FluentIcon.GAME, title='全部已弃置')
        group.addSettingCard(self.relic_salvage_abandon_opt)

        return group

    def on_interface_shown(self) -> None:
        VerticalScrollInterface.on_interface_shown(self)

        self.relic_salvage_level_opt.init_with_adapter(self.ctx.relic_salvage_config.get_prop_adapter('salvage_level'))
        self.relic_salvage_abandon_opt.init_with_adapter(self.ctx.relic_salvage_config.get_prop_adapter('salvage_abandon'))
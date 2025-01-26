import os
from PySide6.QtWidgets import QWidget, QFileDialog
from qfluentwidgets import SettingCardGroup, FluentIcon, PushSettingCard

from phosdeiz.gui.widgets import Column
from one_dragon.gui.widgets.vertical_scroll_interface import VerticalScrollInterface
from one_dragon.gui.widgets.setting_card.combo_box_setting_card import ComboBoxSettingCard
from one_dragon.gui.widgets.setting_card.key_setting_card import KeySettingCard
from one_dragon.gui.widgets.setting_card.switch_setting_card import SwitchSettingCard
from one_dragon.gui.widgets.setting_card.text_setting_card import TextSettingCard
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log
from sr_od.config.game_config import GameRegionEnum, RunModeEnum, TypeInputWay
from sr_od.context.sr_context import SrContext


class SrSettingGameInterface(VerticalScrollInterface):

    def __init__(self, ctx: SrContext, parent=None):
        self.ctx: SrContext = ctx

        VerticalScrollInterface.__init__(
            self,
            object_name='sr_setting_game_interface',
            content_widget=None, parent=parent,
            nav_text_cn='游戏设置'
        )

    def get_content_widget(self) -> QWidget:
        content_widget = Column()

        content_widget.add_widget(self._get_basic_group())
        content_widget.add_widget(self._get_key_group())
        content_widget.add_stretch(1)

        return content_widget

    def _get_basic_group(self) -> QWidget:
        basic_group = SettingCardGroup(gt('游戏基础', 'ui'))

        self.game_path_opt = PushSettingCard(icon=FluentIcon.FOLDER, title='游戏路径', text='选择')
        self.game_path_opt.clicked.connect(self._on_game_path_clicked)
        basic_group.addSettingCard(self.game_path_opt)

        self.game_region_opt = ComboBoxSettingCard(icon=FluentIcon.HOME, title='游戏区服', options_enum=GameRegionEnum)
        basic_group.addSettingCard(self.game_region_opt)

        self.game_account_opt = TextSettingCard(icon=FluentIcon.PEOPLE, title='账号')
        basic_group.addSettingCard(self.game_account_opt)

        self.game_password_opt = TextSettingCard(icon=FluentIcon.EXPRESSIVE_INPUT_ENTRY, title='密码',
                                                 content='放心不会盗你的号 异地登陆需要验证')
        basic_group.addSettingCard(self.game_password_opt)

        self.input_way_opt = ComboBoxSettingCard(icon=FluentIcon.CLIPPING_TOOL, title='输入方式',
                                                 options_enum=TypeInputWay)
        basic_group.addSettingCard(self.input_way_opt)

        self.run_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='疾跑', options_enum=RunModeEnum)
        basic_group.addSettingCard(self.run_opt)

        self.use_quirky_snacks_opt = SwitchSettingCard(icon=FluentIcon.CAFE, title='只用奇巧零食')
        basic_group.addSettingCard(self.use_quirky_snacks_opt)

        return basic_group

    def _get_key_group(self) -> QWidget:
        key_group = SettingCardGroup(gt('游戏按键', 'ui'))

        self.key_interact_opt = KeySettingCard(icon=FluentIcon.GAME, title='交互')
        key_group.addSettingCard(self.key_interact_opt)

        self.key_technique_opt = KeySettingCard(icon=FluentIcon.GAME, title='秘技')
        key_group.addSettingCard(self.key_technique_opt)

        self.key_open_map_opt = KeySettingCard(icon=FluentIcon.GAME, title='地图')
        key_group.addSettingCard(self.key_open_map_opt)

        self.key_esc_opt = KeySettingCard(icon=FluentIcon.GAME, title='返回')
        key_group.addSettingCard(self.key_esc_opt)

        self.key_gameplay_interaction_opt = KeySettingCard(icon=FluentIcon.GAME, title='玩法交互')
        key_group.addSettingCard(self.key_gameplay_interaction_opt)

        return key_group

    def on_interface_shown(self) -> None:
        VerticalScrollInterface.on_interface_shown(self)

        self.game_region_opt.init_with_adapter(self.ctx.game_config.game_region_adapter)
        self.game_account_opt.init_with_adapter(self.ctx.game_config.game_account_adapter)
        self.game_password_opt.init_with_adapter(self.ctx.game_config.game_account_password_adapter)
        self.input_way_opt.init_with_adapter(self.ctx.game_config.type_input_way_adapter)
        self.run_opt.init_with_adapter(self.ctx.game_config.run_mode_adapter)
        self.use_quirky_snacks_opt.init_with_adapter(self.ctx.game_config.use_quirky_snacks_adapter)

        self.game_path_opt.setContent(self.ctx.game_config.game_path)

        self.key_interact_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('key_interact'))
        self.key_technique_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('key_technique'))
        self.key_open_map_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('key_open_map'))
        self.key_esc_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('key_esc'))
        self.key_gameplay_interaction_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('key_gameplay_interaction'))

    def _on_game_path_clicked(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, gt('选择你的 StarRail/launcher.exe'), filter="Exe (*.exe)")
        if file_path is not None and file_path.endswith('.exe'):
            log.info('选择路径 %s', file_path)
            self._on_game_path_chosen(os.path.normpath(file_path))

    def _on_game_path_chosen(self, file_path) -> None:
        self.ctx.game_config.game_path = file_path
        self.game_path_opt.setContent(file_path)

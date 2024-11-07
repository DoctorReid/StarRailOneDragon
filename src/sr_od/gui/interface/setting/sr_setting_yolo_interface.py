from PySide6.QtWidgets import QWidget
from qfluentwidgets import SettingCardGroup, FluentIcon

from one_dragon.base.config.config_item import get_config_item_from_enum
from one_dragon.envs.env_config import ProxyTypeEnum
from one_dragon.gui.component.column_widget import ColumnWidget
from one_dragon.gui.component.interface.vertical_scroll_interface import VerticalScrollInterface
from one_dragon.gui.component.log_display_card import LogDisplayCard
from one_dragon.gui.component.setting_card.combo_box_setting_card import ComboBoxSettingCard
from one_dragon.gui.component.setting_card.switch_setting_card import SwitchSettingCard
from one_dragon.gui.component.setting_card.text_setting_card import TextSettingCard
from one_dragon.gui.component.setting_card.yolo_model_card import ModelDownloadSettingCard
from one_dragon.utils.i18_utils import gt
from one_dragon.yolo.yolo_utils import SR_MODEL_DOWNLOAD_URL
from sr_od.config.yolo_config import get_world_patrol_opts, get_sim_uni_opts
from sr_od.context.sr_context import SrContext


class SrSettingYoloInterface(VerticalScrollInterface):

    def __init__(self, ctx: SrContext, parent=None):
        VerticalScrollInterface.__init__(
            self,
            object_name='sr_setting_yolo_interface',
            content_widget=None, parent=parent,
            nav_text_cn='模型选择'
        )

        self.ctx: SrContext = ctx

    def get_content_widget(self) -> QWidget:
        content_widget = ColumnWidget()

        content_widget.add_widget(self._init_web_group())
        content_widget.add_widget(self._init_model_group())
        content_widget.add_widget(self._init_log_group())
        content_widget.add_stretch(1)

        return content_widget

    def _init_web_group(self) -> SettingCardGroup:
        web_group = SettingCardGroup(gt('网络相关', 'ui'))

        self.proxy_type_opt = ComboBoxSettingCard(
            icon=FluentIcon.GLOBE, title='网络代理', content='免费代理仅能加速工具和模型下载，无法加速代码同步',
            options_enum=ProxyTypeEnum
        )
        self.proxy_type_opt.value_changed.connect(self._on_proxy_type_changed)
        web_group.addSettingCard(self.proxy_type_opt)

        self.personal_proxy_input = TextSettingCard(
            icon=FluentIcon.WIFI, title='个人代理', content='网络代理中选择 个人代理 后生效',
            input_placeholder='http://127.0.0.1:8080'
        )
        self.personal_proxy_input.value_changed.connect(self._on_personal_proxy_changed)
        web_group.addSettingCard(self.personal_proxy_input)

        return web_group

    def _init_model_group(self) -> SettingCardGroup:
        group = SettingCardGroup(gt('模型', 'ui'))

        self.world_patrol_model_opt = ModelDownloadSettingCard(
            ctx=self.ctx, sub_dir='world_patrol', download_url=SR_MODEL_DOWNLOAD_URL,
            icon=FluentIcon.GLOBE, title='锄大地')
        self.world_patrol_model_opt.value_changed.connect(self.on_world_patrol_model_changed)
        group.addSettingCard(self.world_patrol_model_opt)

        self.world_patrol_gpu_opt = SwitchSettingCard(icon=FluentIcon.GAME, title='锄大地-GPU运算')
        group.addSettingCard(self.world_patrol_gpu_opt)

        self.sim_uni_model_opt = ModelDownloadSettingCard(
            ctx=self.ctx, sub_dir='sim_uni', download_url=SR_MODEL_DOWNLOAD_URL,
            icon=FluentIcon.GLOBE, title='模拟宇宙')
        self.sim_uni_model_opt.value_changed.connect(self._on_sim_uni_model_changed)
        group.addSettingCard(self.sim_uni_model_opt)

        self.sim_uni_gpu_opt = SwitchSettingCard(icon=FluentIcon.GAME, title='模拟宇宙-GPU运算')
        group.addSettingCard(self.sim_uni_gpu_opt)

        return group

    def _init_log_group(self) -> SettingCardGroup:
        log_group = SettingCardGroup(gt('安装日志', 'ui'))
        self.log_card = LogDisplayCard()
        log_group.addSettingCard(self.log_card)

        return log_group

    def on_interface_shown(self) -> None:
        VerticalScrollInterface.on_interface_shown(self)
        self._init_world_patrol_opts()
        self._init_sim_uni_model_opts()

        self.world_patrol_gpu_opt.init_with_adapter(self.ctx.yolo_config.world_patrol_gpu_adapter)
        self.sim_uni_gpu_opt.init_with_adapter(self.ctx.yolo_config.sim_uni_gpu_adapter)

        proxy_type = get_config_item_from_enum(ProxyTypeEnum, self.ctx.env_config.proxy_type)
        if proxy_type is not None:
            self.proxy_type_opt.setValue(proxy_type.value)

        self.personal_proxy_input.setValue(self.ctx.env_config.personal_proxy)

        self.log_card.set_update_log(True)

    def on_interface_hidden(self) -> None:
        VerticalScrollInterface.on_interface_hidden(self)
        self.log_card.set_update_log(False)

    def _init_world_patrol_opts(self) -> None:
        self.world_patrol_model_opt.blockSignals(True)
        self.world_patrol_model_opt.set_options_by_list(get_world_patrol_opts())
        self.world_patrol_model_opt.setValue(self.ctx.yolo_config.world_patrol)
        self.world_patrol_model_opt.check_and_update_display()
        self.world_patrol_model_opt.blockSignals(False)

    def _init_sim_uni_model_opts(self) -> None:
        self.sim_uni_model_opt.blockSignals(True)
        self.sim_uni_model_opt.set_options_by_list(get_sim_uni_opts())
        self.sim_uni_model_opt.setValue(self.ctx.yolo_config.sim_uni)
        self.sim_uni_model_opt.check_and_update_display()
        self.sim_uni_model_opt.blockSignals(False)

    def _on_proxy_type_changed(self, index: int, value: str) -> None:
        """
        拉取方式改变
        :param index: 选项下标
        :param value: 值
        :return:
        """
        config_item = get_config_item_from_enum(ProxyTypeEnum, value)
        self.ctx.env_config.proxy_type = config_item.value
        self._on_proxy_changed()

    def _on_personal_proxy_changed(self, value: str) -> None:
        """
        个人代理改变
        :param value: 值
        :return:
        """
        self.ctx.env_config.personal_proxy = value
        self._on_proxy_changed()

    def _on_proxy_changed(self) -> None:
        """
        代理发生改变
        :return:
        """
        self.ctx.git_service.is_proxy_set = False

    def on_world_patrol_model_changed(self, index: int, value: str) -> None:
        self.ctx.yolo_config.world_patrol = value
        self.world_patrol_model_opt.check_and_update_display()

    def _on_sim_uni_model_changed(self, index: int, value: str) -> None:
        self.ctx.yolo_config.sim_uni = value
        self.sim_uni_model_opt.check_and_update_display()

from PySide6.QtWidgets import QWidget
from qfluentwidgets import SettingCardGroup, FluentIcon, HyperlinkCard

from one_dragon.utils.i18_utils import gt
from one_dragon_qt.widgets.column import Column
from one_dragon_qt.widgets.vertical_scroll_interface import VerticalScrollInterface
from one_dragon_qt.widgets.log_display_card import LogDisplayCard
from one_dragon_qt.widgets.setting_card.onnx_model_download_card import OnnxModelDownloadCard
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
        content_widget = Column()

        content_widget.add_widget(self._init_model_group())
        content_widget.add_widget(self._init_log_group())
        content_widget.add_stretch(1)

        return content_widget
    def _init_model_group(self) -> SettingCardGroup:
        group = SettingCardGroup(gt('模型', 'ui'))

        self.help_opt = HyperlinkCard(icon=FluentIcon.HELP, title='下载说明', text='',
                                      url='')
        self.help_opt.linkButton.hide()
        self.help_opt.setContent('下载失败时 请尝试到「脚本环境」更改网络代理')
        group.addSettingCard(self.help_opt)

        self.world_patrol_model_opt = OnnxModelDownloadCard(ctx=self.ctx, icon=FluentIcon.GLOBE, title='锄大地')
        self.world_patrol_model_opt.value_changed.connect(self.on_world_patrol_model_changed)
        self.world_patrol_model_opt.gpu_changed.connect(self.on_world_patrol_gpu_changed)
        group.addSettingCard(self.world_patrol_model_opt)

        self.sim_uni_model_opt = OnnxModelDownloadCard(ctx=self.ctx, icon=FluentIcon.GLOBE, title='模拟宇宙')
        self.sim_uni_model_opt.value_changed.connect(self._on_sim_uni_model_changed)
        self.sim_uni_model_opt.gpu_changed.connect(self.on_sim_uni_gpu_changed)
        group.addSettingCard(self.sim_uni_model_opt)

        return group

    def _init_log_group(self) -> SettingCardGroup:
        log_group = SettingCardGroup(gt('安装日志', 'ui'))
        self.log_card = LogDisplayCard()
        log_group.addSettingCard(self.log_card)

        return log_group

    def on_interface_shown(self) -> None:
        VerticalScrollInterface.on_interface_shown(self)

        self.init_world_patrol_opts()
        self.init_sim_uni_model_opts()

        self.log_card.start()

    def on_interface_hidden(self) -> None:
        VerticalScrollInterface.on_interface_hidden(self)
        self.log_card.stop()

    def init_world_patrol_opts(self) -> None:
        self.world_patrol_model_opt.blockSignals(True)
        self.world_patrol_model_opt.set_options_by_list(get_world_patrol_opts())
        self.world_patrol_model_opt.setValue(self.ctx.yolo_config.world_patrol)
        self.world_patrol_model_opt.gpu_opt.setChecked(self.ctx.yolo_config.world_patrol_gpu)
        self.world_patrol_model_opt.check_and_update_display()
        self.world_patrol_model_opt.blockSignals(False)

    def init_sim_uni_model_opts(self) -> None:
        self.sim_uni_model_opt.blockSignals(True)
        self.sim_uni_model_opt.set_options_by_list(get_sim_uni_opts())
        self.sim_uni_model_opt.setValue(self.ctx.yolo_config.sim_uni)
        self.sim_uni_model_opt.gpu_opt.setChecked(self.ctx.yolo_config.sim_uni_gpu)
        self.sim_uni_model_opt.check_and_update_display()
        self.sim_uni_model_opt.blockSignals(False)

    def on_world_patrol_model_changed(self, index: int, value: str) -> None:
        self.ctx.yolo_config.world_patrol = value
        self.world_patrol_model_opt.check_and_update_display()

    def on_world_patrol_gpu_changed(self, value: bool) -> None:
        self.ctx.yolo_config.world_patrol_gpu = value

    def _on_sim_uni_model_changed(self, index: int, value: str) -> None:
        self.ctx.yolo_config.sim_uni = value
        self.sim_uni_model_opt.check_and_update_display()

    def on_sim_uni_gpu_changed(self, value: bool) -> None:
        self.ctx.yolo_config.sim_uni_gpu = value

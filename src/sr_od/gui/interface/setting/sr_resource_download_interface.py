from PySide6.QtWidgets import QWidget
from qfluentwidgets import SettingCardGroup, FluentIcon

from one_dragon.base.web.common_downloader import CommonDownloaderParam
from one_dragon_qt.view.setting.resource_download_interface import ResourceDownloadInterface
from one_dragon_qt.widgets.setting_card.onnx_model_download_card import OnnxModelDownloadCard
from sr_od.config.model_config import get_world_patrol_opts, get_sim_uni_opts
from sr_od.context.sr_context import SrContext


class SrResourceDownloadInterface(ResourceDownloadInterface):

    def __init__(self, ctx: SrContext, parent=None):
        ResourceDownloadInterface.__init__(self, ctx, parent)
        self.ctx: SrContext = ctx

    def _add_model_cards(self, group: SettingCardGroup) -> None:

        self.world_patrol_model_opt = OnnxModelDownloadCard(ctx=self.ctx, icon=FluentIcon.GLOBE, title='锄大地')
        self.world_patrol_model_opt.value_changed.connect(self.on_world_patrol_model_changed)
        self.world_patrol_model_opt.gpu_changed.connect(self.on_world_patrol_gpu_changed)
        group.addSettingCard(self.world_patrol_model_opt)

        self.sim_uni_model_opt = OnnxModelDownloadCard(ctx=self.ctx, icon=FluentIcon.GLOBE, title='模拟宇宙')
        self.sim_uni_model_opt.value_changed.connect(self._on_sim_uni_model_changed)
        self.sim_uni_model_opt.gpu_changed.connect(self.on_sim_uni_gpu_changed)
        group.addSettingCard(self.sim_uni_model_opt)

    def _set_log_card_height(self, log_card: QWidget) -> None:
        log_card.setFixedHeight(238)

    def on_interface_shown(self) -> None:
        ResourceDownloadInterface.on_interface_shown(self)

        self.init_world_patrol_opts()
        self.init_sim_uni_model_opts()

    def init_world_patrol_opts(self) -> None:
        self.world_patrol_model_opt.blockSignals(True)
        self.world_patrol_model_opt.set_options_by_list(get_world_patrol_opts())
        self.world_patrol_model_opt.set_value_by_save_file_name(f'{self.ctx.model_config.world_patrol}.zip')
        self.world_patrol_model_opt.gpu_opt.setChecked(self.ctx.model_config.world_patrol_gpu)
        self.world_patrol_model_opt.check_and_update_display()
        self.world_patrol_model_opt.blockSignals(False)

    def init_sim_uni_model_opts(self) -> None:
        self.sim_uni_model_opt.blockSignals(True)
        self.sim_uni_model_opt.set_options_by_list(get_sim_uni_opts())
        self.sim_uni_model_opt.set_value_by_save_file_name(f'{self.ctx.model_config.sim_uni}.zip')
        self.sim_uni_model_opt.gpu_opt.setChecked(self.ctx.model_config.sim_uni_gpu)
        self.sim_uni_model_opt.check_and_update_display()
        self.sim_uni_model_opt.blockSignals(False)

    def on_world_patrol_model_changed(self, index: int, value: CommonDownloaderParam) -> None:
        self.ctx.model_config.world_patrol = value.save_file_name[:-4]
        self.world_patrol_model_opt.check_and_update_display()

    def on_world_patrol_gpu_changed(self, value: bool) -> None:
        self.ctx.model_config.world_patrol_gpu = value

    def _on_sim_uni_model_changed(self, index: int, value: CommonDownloaderParam) -> None:
        self.ctx.model_config.sim_uni = value.save_file_name[:-4]
        self.sim_uni_model_opt.check_and_update_display()

    def on_sim_uni_gpu_changed(self, value: bool) -> None:
        self.ctx.model_config.sim_uni_gpu = value


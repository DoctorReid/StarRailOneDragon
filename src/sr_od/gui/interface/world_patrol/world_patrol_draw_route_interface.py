import time

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from cv2.typing import MatLike
from qfluentwidgets import PushButton, PlainTextEdit, SettingCardGroup, FluentIcon
from sympy.codegen.ast import continue_
from typing import Optional, List, Tuple

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.base.geometry.point import Point
from one_dragon.base.matcher.match_result import MatchResult
from one_dragon.base.operation.context_event_bus import ContextEventItem
from one_dragon.base.operation.one_dragon_context import ContextKeyboardEventEnum
from one_dragon.gui.component.combo_box import ComboBox
from one_dragon.gui.component.cv2_image import Cv2Image
from one_dragon.gui.component.interface.vertical_scroll_interface import VerticalScrollInterface
from one_dragon.gui.component.label.click_image_label import ClickImageLabel, ImageScaleEnum
from one_dragon.gui.component.row_widget import RowWidget
from one_dragon.gui.component.setting_card.combo_box_setting_card import ComboBoxSettingCard
from one_dragon.utils.i18_utils import gt
from sr_od.app.world_patrol import world_patrol_route_draw_utils
from sr_od.app.world_patrol.world_patrol_route import WorldPatrolRoute
from sr_od.app.world_patrol.world_patrol_route_draw_utils import can_change_tp
from sr_od.app.world_patrol.world_patrol_whitelist_config import create_new_whitelist
from sr_od.context.sr_context import SrContext
from sr_od.operations.move import cal_pos_utils
from sr_od.sr_map import mini_map_utils, large_map_utils
from sr_od.sr_map.sr_map_def import Planet, Region, SpecialPoint


class WorldPatrolDrawRouteInterface(VerticalScrollInterface):

    def __init__(self, ctx: SrContext, parent=None):
        self.ctx: SrContext = ctx

        VerticalScrollInterface.__init__(
            self,
            object_name='sr_world_patrol_draw_route_interface',
            content_widget=None, parent=parent,
            nav_text_cn='路线绘制'
        )

        self.chosen_planet: Optional[Planet] = None
        self.chosen_region_without_level: Optional[Region] = None
        self.chosen_region_with_level: Optional[Region] = None
        self.chosen_tp: Optional[SpecialPoint] = None
        self.chosen_route: Optional[WorldPatrolRoute] = None

    def get_content_widget(self) -> QWidget:
        """
        子界面内的内容组件 由子类实现
        :return:
        """
        content_widget = QWidget()
        # 创建 QVBoxLayout 作为主布局
        main_layout = QVBoxLayout(content_widget)

        # 创建 QHBoxLayout 作为中间布局
        horizontal_layout = QHBoxLayout()

        # 将 QVBoxLayouts 加入 QHBoxLayout
        horizontal_layout.addLayout(self.get_left_layout())
        horizontal_layout.addLayout(self.get_middle_layout())
        horizontal_layout.addLayout(self.get_right_layout())
        horizontal_layout.addStretch(1)

        # 确保 QHBoxLayout 可以伸缩
        horizontal_layout.setSpacing(10)
        horizontal_layout.setContentsMargins(0, 0, 0, 0)

        # 设置伸缩因子，让 QHBoxLayout 占据空间
        main_layout.addLayout(horizontal_layout, stretch=1)

        return content_widget

    def get_left_layout(self) -> QVBoxLayout:
        layout = QVBoxLayout()

        # 区域行
        region_row = RowWidget()

        self.planet_btn = ComboBox()
        self.planet_btn.setPlaceholderText(gt('选择星球', 'ui'))
        self.planet_btn.currentIndexChanged.connect(self.on_planet_changed)
        region_row.add_widget(self.planet_btn)

        self.region_without_level_opt = ComboBox()
        self.region_without_level_opt.setPlaceholderText(gt('选择区域', 'ui'))
        self.region_without_level_opt.currentIndexChanged.connect(self.on_region_without_level_selected)
        region_row.add_widget(self.region_without_level_opt)

        self.region_level_opt = ComboBox()
        self.region_level_opt.setPlaceholderText(gt('选择区域楼层', 'ui'))
        self.region_level_opt.currentIndexChanged.connect(self.on_region_level_selected)
        region_row.add_widget(self.region_level_opt)

        region_row.add_stretch(1)
        layout.addWidget(region_row)

        # 传送点行
        tp_row = RowWidget()

        self.tp_opt = ComboBox()
        self.tp_opt.setPlaceholderText(gt('选择传送点', 'ui'))
        self.tp_opt.currentIndexChanged.connect(self.on_tp_changed)
        tp_row.add_widget(self.tp_opt)

        tp_row.add_stretch(1)
        layout.addWidget(tp_row)

        # 路线行
        route_row = RowWidget()

        self.existed_route_opt = ComboBox()
        self.existed_route_opt.setPlaceholderText(gt('选择路线', 'ui'))
        self.existed_route_opt.currentIndexChanged.connect(self.on_route_selected)
        route_row.add_widget(self.existed_route_opt)

        route_row.add_stretch(1)
        layout.addWidget(route_row)

        # 保存按钮行
        save_btn_row = RowWidget()

        self.create_btn = PushButton(text=gt('新建', 'ui'))
        self.create_btn.clicked.connect(self.on_create_clicked)
        save_btn_row.add_widget(self.create_btn)

        self.save_btn = PushButton(text=gt('保存', 'ui'))
        self.save_btn.clicked.connect(self.on_save_clicked)
        save_btn_row.add_widget(self.save_btn)

        self.delete_btn = PushButton(text=gt('删除', 'ui'))
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        save_btn_row.add_widget(self.delete_btn)

        self.cancel_btn = PushButton(text=gt('取消', 'ui'))
        self.cancel_btn.clicked.connect(self.on_cancel_clicked)
        save_btn_row.add_widget(self.cancel_btn)

        self.back_btn = PushButton(text=gt('回退 -'))
        self.back_btn.clicked.connect(self.on_back_clicked)
        save_btn_row.add_widget(self.back_btn)

        save_btn_row.add_stretch(1)
        layout.addWidget(save_btn_row)

        # 位置相关的按钮行
        pos_row = RowWidget()

        self.cal_move_btn = PushButton(text=gt('截图移动 Q'))
        self.cal_move_btn.clicked.connect(self.on_cal_move_clicked)
        pos_row.add_widget(self.cal_move_btn)

        self.slow_move_btn = PushButton(text=gt('禁疾跑'))
        self.slow_move_btn.clicked.connect(self.on_slow_move_clicked)
        pos_row.add_widget(self.slow_move_btn)

        self.update_pos_btn = PushButton(text=gt('更新位置'))
        self.update_pos_btn.clicked.connect(self.on_update_pos_clicked)
        pos_row.add_widget(self.update_pos_btn)

        pos_row.add_stretch(1)
        layout.addWidget(pos_row)

        layout.addStretch(1)

        return layout

    def get_middle_layout(self) -> QVBoxLayout:
        layout = QVBoxLayout()

        layout.addWidget(SettingCardGroup('路线指令'))
        self.route_text = PlainTextEdit()
        self.route_text.setMinimumWidth(200)
        self.route_text.setMinimumHeight(700)
        layout.addWidget(self.route_text)

        layout.addStretch(1)

        return layout

    def get_right_layout(self) -> QVBoxLayout:
        layout = QVBoxLayout()

        layout.addWidget(SettingCardGroup('大地图'))

        self.image_size_opt = ComboBoxSettingCard(
            icon=FluentIcon.ZOOM_IN, title='图片显示大小',
            options_enum=ImageScaleEnum
        )
        self.image_size_opt.setValue(1)
        self.image_size_opt.value_changed.connect(self.on_image_size_chosen)
        layout.addWidget(self.image_size_opt)

        self.large_map_image = ClickImageLabel()
        self.large_map_image.clicked_with_pos.connect(self.on_large_map_clicked)
        layout.addWidget(self.large_map_image)

        layout.addStretch(1)

        return layout

    def on_interface_shown(self) -> None:
        VerticalScrollInterface.on_interface_shown(self)

        self.ctx.map_data.load_map_data()
        self.update_planet_opt()
        self.update_region_without_level_opt()
        self.update_region_with_level_opt()
        self.update_tp_opt()
        self.update_existed_route_opt()
        self.update_display_by_route()

        self.ctx.listen_event(ContextKeyboardEventEnum.PRESS.value, self.on_key_press)

    def on_interface_hidden(self) -> None:
        VerticalScrollInterface.on_interface_hidden(self)
        self.ctx.unlisten_all_event(self)

    def update_display_by_route(self) -> None:
        """
        根据选择配置更新显示
        :return:
        """
        chosen = self.chosen_route is not None

        self.create_btn.setDisabled(chosen)
        self.save_btn.setDisabled(not chosen)
        self.delete_btn.setDisabled(not chosen)
        self.cancel_btn.setDisabled(not chosen)
        self.back_btn.setDisabled(not chosen)

        can_change_tp = world_patrol_route_draw_utils.can_change_tp(self.chosen_route)
        self.planet_btn.setDisabled(not can_change_tp)
        self.region_without_level_opt.setDisabled(not can_change_tp)
        self.tp_opt.setDisabled(not can_change_tp)

        self.slow_move_btn.setDisabled(not chosen)
        self.update_pos_btn.setDisabled(not chosen)

        self.route_text.setDisabled(not chosen)
        self.update_large_map_image()

        if chosen:
            self.route_text.setPlainText(self.chosen_route.route_config_str)
        else:
            self.route_text.setPlainText('')

    def update_planet_opt(self) -> None:
        """
        更新星球选项
        :return:
        """
        if self.chosen_planet is None:
            self.chosen_planet = self.ctx.map_data.planet_list[0]

        self.planet_btn.set_items(
            [ConfigItem(i.display_name, i) for i in self.ctx.map_data.planet_list],
            target_value=self.chosen_planet
        )

    def update_region_without_level_opt(self) -> None:
        """
        更新区域选项
        :return:
        """
        region_list: List[Region] = []
        for region in self.ctx.map_data.region_list:
            if self.chosen_planet is not None and region.planet.np_id != self.chosen_planet.np_id:
                continue

            # 多个楼层只选择一个
            existed = False
            for existed_region in region_list:
                if region.pr_id == existed_region.pr_id:
                    existed = True
                    break
            if existed:
                continue

            region_list.append(region)

        if self.chosen_region_without_level is None:
            self.chosen_region_without_level = region_list[0]

        self.region_without_level_opt.set_items(
            [ConfigItem(gt(r.cn), r) for r in region_list],
            self.chosen_region_without_level
        )

    def update_region_with_level_opt(self) -> None:
        region_list = self.ctx.map_data.get_region_with_all_floor(self.chosen_region_without_level)
        config_list = [ConfigItem(str(r.floor), r) for r in region_list]

        if self.chosen_route is not None:
            region, _ = world_patrol_route_draw_utils.get_last_pos(self.ctx, self.chosen_route)
            self.chosen_region_with_level = self.ctx.map_data.region_with_another_floor(
                self.chosen_region_without_level, region.floor)
        elif self.chosen_region_with_level is None or self.chosen_region_with_level.pr_id != self.chosen_region_without_level.pr_id:
            self.chosen_region_with_level = region_list[0]

        self.region_level_opt.set_items(config_list, self.chosen_region_with_level)

    def update_tp_opt(self) -> None:
        if self.chosen_region_without_level is not None or self.chosen_region_with_level is not None:
            region = self.chosen_region_without_level
            if self.chosen_region_with_level is not None and self.chosen_region_with_level.pr_id == region.pr_id:
                region = self.chosen_region_with_level

            config_list = []
            sp_list = self.ctx.map_data.region_2_sp.get(region.pr_id, [])
            for sp in sp_list:
                if not sp.template_id.startswith('mm_tp') and not sp.template_id.startswith('mm_boss'):
                    continue
                config_list.append(ConfigItem(sp.display_name, sp))

            if len(config_list) > 0 and (
                    self.chosen_tp is None
                    or self.chosen_tp.region.pr_id != region.pr_id
            ):
                self.chosen_tp = config_list[0].value
            self.tp_opt.set_items(config_list, self.chosen_tp)
        else:
            self.tp_opt.set_items([])

    def update_existed_route_opt(self) -> None:
        """
        更新路线选项
        :return:
        """
        region = self.chosen_region_without_level
        if self.chosen_region_with_level is not None:
            region = self.chosen_region_with_level
        route_list = self.ctx.world_patrol_route_data.load_all_route(
            target_planet=self.chosen_planet,
            target_region=region
        )

        config_list = []
        for i in route_list:
            config_list.append(ConfigItem(i.display_name, i))

            if self.chosen_route is not None and self.chosen_route.unique_id == i.unique_id:
                self.chosen_route = i

        self.existed_route_opt.set_items(config_list, self.chosen_route)

    def update_large_map_image(self) -> None:
        if self.chosen_route is None:
            if self.chosen_tp is None:
                region = self.chosen_region_without_level
                if self.chosen_region_with_level is not None:
                    region = self.chosen_region_with_level
                if region is not None:
                    lm_info = self.ctx.map_data.get_large_map_info(region)
                    if lm_info.raw is None:
                        img = QImage()
                    else:
                        img_to_show = lm_info.raw.copy()
                        img = Cv2Image(img_to_show)
                else:
                    img = QImage()
            else:
                route = WorldPatrolRoute(self.chosen_tp, {
                    "author": [],
                    "route": []
                }, '')
                img_to_show = world_patrol_route_draw_utils.get_route_image(self.ctx, route)
                img = Cv2Image(img_to_show)
        else:
            img_to_show = world_patrol_route_draw_utils.get_route_image(self.ctx, self.chosen_route)
            img = Cv2Image(img_to_show)

        self.large_map_image.setImage(img)
        size_value: float = self.image_size_opt.combo_box.currentData()
        if size_value is None:
            display_width = img.width()
            display_height = img.height()
        else:
            display_width = int(img.width() * size_value)
            display_height = int(img.height() * size_value)
        self.large_map_image.setFixedSize(display_width, display_height)

    def on_route_selected(self, idx: int) -> None:
        self.chosen_route = self.existed_route_opt.itemData(idx)
        
        if self.chosen_planet is None:
            planet = self.chosen_route.tp.region.planet
            self.chosen_planet = planet
            self.update_planet_opt()
            self.chosen_planet = self.planet_btn.currentData()

        if self.chosen_region_without_level is None:
            region = self.chosen_route.tp.region
            self.chosen_region_without_level = region
            self.update_region_without_level_opt()
            self.chosen_region_without_level = self.region_without_level_opt.currentData()

        if self.chosen_region_with_level is None:
            region, _ = world_patrol_route_draw_utils.get_last_pos(self.ctx, self.chosen_route)
            self.chosen_region_with_level = region
            self.update_region_with_level_opt()
            self.chosen_region_with_level = self.region_level_opt.currentData()
        
        self.update_display_by_route()

    def on_create_clicked(self) -> None:
        if self.chosen_route is not None:
            return

        self.chosen_route = create_new_whitelist()
        self.update_display_by_route()

    def on_save_clicked(self) -> None:
        if self.chosen_route is None:
            return

    def on_delete_clicked(self):
        if self.chosen_route is None:
            return
        self.chosen_route.delete()

        self.chosen_route = None
        self.existed_route_opt.setCurrentIndex(-1)
        self.update_display_by_route()

    def on_cancel_clicked(self):
        self.chosen_route = None
        self.existed_route_opt.setCurrentIndex(-1)
        self.update_display_by_route()

    def on_planet_changed(self, idx: int) -> None:
        self.chosen_planet = self.planet_btn.itemData(idx)
        self.update_region_without_level_opt()
        self.update_region_with_level_opt()
        self.update_tp_opt()
        self.update_existed_route_opt()
        self.update_large_map_image()

    def on_region_without_level_selected(self, idx: int) -> None:
        self.chosen_region_without_level = self.region_without_level_opt.itemData(idx)
        self.update_region_with_level_opt()
        self.update_tp_opt()
        self.update_existed_route_opt()
        self.update_large_map_image()

    def on_region_level_selected(self, idx: int) -> None:
        self.chosen_region_with_level = self.region_level_opt.itemData(idx)
        self.update_tp_opt()
        self.update_existed_route_opt()
        self.update_large_map_image()
        self.update_large_map_image()

    def on_tp_changed(self, idx: int) -> None:
        self.chosen_tp = self.tp_opt.currentData()
        self.update_large_map_image()

    def on_image_size_chosen(self) -> None:
        self.update_large_map_image()

    def get_region_level(self) -> Optional[int]:
        """
        获取当前选择的区域楼层
        :return:
        """
        floor: Optional[int] = None
        if self.chosen_region_without_level is not None:
            floor = self.chosen_region_without_level.floor
        if self.chosen_region_with_level is not None:
            floor = self.chosen_region_with_level.floor
        return floor

    def on_large_map_clicked(self, x: int, y: int) -> None:
        if self.chosen_route is None:
            return

        display_width = self.large_map_image.width()
        display_height = self.large_map_image.height()

        lm_info = self.ctx.map_data.get_large_map_info(self.chosen_route.tp.region)
        image_width = lm_info.raw.shape[1]
        image_height = lm_info.raw.shape[0]

        real_x = int(x * image_width / display_width)
        real_y = int(y * image_height / display_height)

        world_patrol_route_draw_utils.add_move(self.ctx, self.chosen_route,
                                               real_x, real_y, self.get_region_level())
        self.update_display_by_route()

    def on_key_press(self, event: ContextEventItem) -> None:
        key: str = event.data
        if key == '-':
            self.on_back_clicked()
        elif key == 'q':
            self.on_cal_move_clicked()

    def on_back_clicked(self) -> None:
        if self.chosen_route is None:
            return

        world_patrol_route_draw_utils.pop_last(self.chosen_route)
        self.update_display_by_route()

    def on_slow_move_clicked(self) -> None:
        if self.chosen_route is None:
            return

        world_patrol_route_draw_utils.mark_last_move_as_slow(self.chosen_route)
        self.update_display_by_route()

    def on_update_pos_clicked(self) -> None:
        if self.chosen_route is None:
            return

        world_patrol_route_draw_utils.mark_last_move_as_update(self.chosen_route)
        self.update_display_by_route()

    def on_cal_move_clicked(self) -> None:
        if self.chosen_route is None:
            return

        next_region, next_pos = self.cal_pos_by_screenshot()

        self.chosen_region_with_level = next_region
        world_patrol_route_draw_utils.add_move(self.ctx, self.chosen_route,
                                               next_pos.x, next_pos.y,
                                               self.get_region_level())
        self.update_display_by_route()

    def cal_pos_by_screenshot(self) -> Tuple[Optional[Region], Optional[Point]]:
        region, last_pos = world_patrol_route_draw_utils.get_last_pos(self.ctx, self.chosen_route)
        lm_info = self.ctx.map_data.get_large_map_info(region)
        next_region = region

        if not self.ctx.controller.game_win.is_win_active:
            self.ctx.controller.active_window()
            time.sleep(1)
        screen = self.ctx.controller.screenshot(True)
        mm = mini_map_utils.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
        mm_info = mini_map_utils.analyse_mini_map(mm)

        next_pos: Optional[MatchResult] = None

        for move_time in range(1, 10):
            move_distance = self.ctx.controller.cal_move_distance_by_time(move_time)
            possible_pos = (last_pos.x, last_pos.y, move_distance)
            lm_rect = large_map_utils.get_large_map_rect_by_pos(lm_info.gray.shape, mm.shape[:2], possible_pos)

            next_pos = cal_pos_utils.cal_character_pos(
                self.ctx, lm_info, mm_info,
                lm_rect=lm_rect, retry_without_rect=False,
                running=self.ctx.controller.is_moving,
                real_move_time=move_time)

            if next_pos is None and region.floor != 0:
                region_list = self.ctx.map_data.get_region_with_all_floor(region)
                for another_floor_region in region_list:
                    if another_floor_region.floor == region.floor:
                        continue

                    next_lm_info = self.ctx.map_data.get_large_map_info(another_floor_region)
                    next_pos = cal_pos_utils.cal_character_pos(
                        self.ctx, next_lm_info, mm_info,
                        lm_rect=lm_rect, retry_without_rect=False,
                        running=self.ctx.controller.is_moving,
                        real_move_time=move_time)

                    if next_pos is not None:
                        next_region = another_floor_region
                        break

            if next_pos is not None:
                break

        return next_region, next_pos

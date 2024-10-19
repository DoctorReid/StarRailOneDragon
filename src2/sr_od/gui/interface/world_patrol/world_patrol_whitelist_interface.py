from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidgetItem
from qfluentwidgets import ComboBox, PushButton, TableWidget, ToolButton, FluentIcon
from typing import Optional, List

from one_dragon.gui.component.interface.vertical_scroll_interface import VerticalScrollInterface
from one_dragon.gui.component.row_widget import RowWidget
from one_dragon.gui.component.setting_card.combo_box_setting_card import ComboBoxSettingCard
from one_dragon.gui.component.setting_card.text_setting_card import TextSettingCard
from one_dragon.utils.i18_utils import gt
from sr_od.context.sr_context import SrContext
from sr_od.sr_map.sr_map_def import Planet, Region
from sr_od.app.world_patrol.world_patrol_route import WorldPatrolRoute
from sr_od.app.world_patrol.world_patrol_whitelist_config import WorldPatrolWhitelist, create_new_whitelist, \
    load_all_whitelist_list, WorldPatrolWhiteListType


class WorldPatrolWhitelistInterface(VerticalScrollInterface):

    def __init__(self, ctx: SrContext, parent=None):
        self.ctx: SrContext = ctx

        VerticalScrollInterface.__init__(
            self,
            object_name='sr_world_patrol_whitelist_interface',
            content_widget=None, parent=parent,
            nav_text_cn='名单列表'
        )

        self.chosen_config: Optional[WorldPatrolWhitelist] = None
        self.chosen_planet: Optional[Planet] = None
        self.chosen_region: Optional[Region] = None
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
        horizontal_layout.addLayout(self.get_left_layout(), stretch=1)
        horizontal_layout.addLayout(self.get_right_layout(), stretch=1)

        # 确保 QHBoxLayout 可以伸缩
        horizontal_layout.setSpacing(0)
        horizontal_layout.setContentsMargins(0, 0, 0, 0)

        # 设置伸缩因子，让 QHBoxLayout 占据空间
        main_layout.addLayout(horizontal_layout, stretch=1)

        return content_widget

    def get_left_layout(self) -> QVBoxLayout:
        layout = QVBoxLayout()

        # 按键行
        btn_row = RowWidget()
        layout.addWidget(btn_row)

        self.existed_yml_btn = ComboBox()
        self.existed_yml_btn.setPlaceholderText(gt('选择已有', 'ui'))
        btn_row.add_widget(self.existed_yml_btn)

        self.create_btn = PushButton(text=gt('新建', 'ui'))
        self.create_btn.clicked.connect(self.on_create_clicked)
        btn_row.add_widget(self.create_btn)

        self.delete_btn = PushButton(text=gt('删除', 'ui'))
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        btn_row.add_widget(self.delete_btn)

        self.cancel_btn = PushButton(text=gt('取消', 'ui'))
        self.cancel_btn.clicked.connect(self.on_cancel_clicked)
        btn_row.add_widget(self.cancel_btn)

        btn_row.add_stretch(1)

        # 选择路线行
        route_row = RowWidget()
        layout.addWidget(route_row)

        self.planet_btn = ComboBox()
        self.planet_btn.setPlaceholderText(gt('选择星球', 'ui'))
        route_row.add_widget(self.planet_btn)

        self.region_btn = ComboBox()
        self.region_btn.setPlaceholderText(gt('选择区域', 'ui'))
        route_row.add_widget(self.region_btn)

        self.route_btn = ComboBox()
        self.route_btn.setPlaceholderText(gt('选择路线', 'ui'))
        route_row.add_widget(self.route_btn)

        route_row.add_stretch(1)

        # 增加按钮行
        add_row = RowWidget()
        layout.addWidget(add_row)

        self.add_planet_btn = PushButton(text=gt('添加星球', 'ui'))
        self.add_planet_btn.clicked.connect(self.on_add_planet_clicked)
        add_row.add_widget(self.add_planet_btn)

        self.add_region_btn = PushButton(text=gt('添加区域', 'ui'))
        self.add_region_btn.clicked.connect(self.on_add_region_clicked)
        add_row.add_widget(self.add_region_btn)

        self.add_route_btn = PushButton(text=gt('添加路线', 'ui'))
        self.add_route_btn.clicked.connect(self.on_add_route_clicked)
        add_row.add_widget(self.add_route_btn)

        add_row.add_stretch(1)

        self.whitelist_name_opt = TextSettingCard(icon=FluentIcon.INFO, title='名单名称')
        layout.addWidget(self.whitelist_name_opt)

        self.type_opt = ComboBoxSettingCard(icon=FluentIcon.INFO, title='名单类型',
                                            options_enum=WorldPatrolWhiteListType)
        layout.addWidget(self.type_opt)

        layout.addStretch(1)

        return layout

    def get_right_layout(self) -> QVBoxLayout:
        layout = QVBoxLayout()

        self.route_table = TableWidget()
        self.route_table.verticalHeader().hide()
        self.route_table.setColumnCount(2)
        self.route_table.setColumnWidth(0, 350)
        self.route_table.setColumnWidth(1, 50)
        self.route_table.setHorizontalHeaderLabels([
            gt('路线', 'ui'),
            gt('删除', 'ui'),
        ])
        self.route_table.setMinimumHeight(600)

        layout.addWidget(self.route_table)
        layout.addStretch(1)

        return layout

    def on_interface_shown(self) -> None:
        VerticalScrollInterface.on_interface_shown(self)

        self.update_display_by_config()

        self.ctx.world_patrol_map_data.load_map_data()
        self.update_planet_opt()
        self.update_region_opt()

    def update_display_by_config(self) -> None:
        """
        根据选择配置更新显示
        :return:
        """
        chosen = self.chosen_config is not None

        self.update_existed_opt()
        self.create_btn.setDisabled(chosen)
        self.delete_btn.setDisabled(not chosen)
        self.cancel_btn.setDisabled(not chosen)

        self.planet_btn.setDisabled(not chosen)
        self.region_btn.setDisabled(not chosen)
        self.route_btn.setDisabled(not chosen)

        self.whitelist_name_opt.setDisabled(not chosen)
        self.type_opt.setDisabled(not chosen)

        if chosen:
            self.whitelist_name_opt.init_with_adapter(self.chosen_config.name_adapter)
            self.type_opt.init_with_adapter(self.chosen_config.type_adapter)
        else:
            self.whitelist_name_opt.init_with_adapter(None)
            self.type_opt.init_with_adapter(None)

        self.update_route_table()

    def update_existed_opt(self) -> None:
        """
        更新已有列表选项
        :return:
        """
        try:
            # 更新之前 先取消原来的监听 防止触发事件
            self.existed_yml_btn.currentIndexChanged.disconnect(self.on_choose_existed)
        except Exception:
            pass

        self.existed_yml_btn.clear()

        config_name_list = load_all_whitelist_list()
        target_idx: int = -1
        for idx in range(len(config_name_list)):
            config_name = config_name_list[idx]
            if self.chosen_config is not None and config_name == self.chosen_config.old_module_name:
                target_idx = idx
            config = WorldPatrolWhitelist(config_name)
            self.existed_yml_btn.addItem(text=config.name, icon=None, userData=config)

        self.existed_yml_btn.setCurrentIndex(target_idx)

        self.existed_yml_btn.setDisabled(self.chosen_config is not None)
        self.existed_yml_btn.currentIndexChanged.connect(self.on_choose_existed)

    def update_planet_opt(self) -> None:
        """
        更新星球选项
        :return:
        """
        try:
            # 更新之前 先取消原来的监听 防止触发事件
            self.planet_btn.currentIndexChanged.disconnect(self.on_choose_planet)
        except Exception:
            pass

        self.planet_btn.clear()

        target_idx: int = -1
        for idx in range(len(self.ctx.world_patrol_map_data.planet_list)):
            planet = self.ctx.world_patrol_map_data.planet_list[idx]
            if self.chosen_planet is not None and planet.np_id == self.chosen_planet.np_id:
                target_idx = idx
            self.planet_btn.addItem(text=planet.display_name, icon=None, userData=planet)

        self.planet_btn.setCurrentIndex(target_idx)

        self.planet_btn.currentIndexChanged.connect(self.on_choose_planet)

    def update_region_opt(self) -> None:
        """
        更新区域选项
        :return:
        """
        try:
            # 更新之前 先取消原来的监听 防止触发事件
            self.region_btn.currentIndexChanged.disconnect(self.on_choose_region)
        except Exception:
            pass

        self.region_btn.clear()

        target_idx: int = -1
        region_list: List[Region] = []

        for region in self.ctx.world_patrol_map_data.region_list:
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

        for idx in range(len(region_list)):
            region = region_list[idx]
            if self.chosen_region is not None and region.pr_id == self.chosen_region.pr_id:
                target_idx = idx
            self.region_btn.addItem(text=region.display_name, icon=None, userData=region)

        self.region_btn.setCurrentIndex(target_idx)

        self.region_btn.currentIndexChanged.connect(self.on_choose_region)

    def update_route_opt(self) -> None:
        """
        更新路线选项
        :return:
        """
        try:
            # 更新之前 先取消原来的监听 防止触发事件
            self.route_btn.currentIndexChanged.disconnect(self.on_choose_route)
        except Exception:
            pass

        self.route_btn.clear()

        target_idx: int = -1
        route_list: List[WorldPatrolRoute] = []

        if self.chosen_region is not None:
            route_list = self.ctx.world_patrol_route_data.load_all_route(target_region=self.chosen_region)

        for idx in range(len(route_list)):
            route = route_list[idx]
            if self.chosen_route is not None and route.unique_id == self.chosen_route.unique_id:
                target_idx = idx
            self.route_btn.addItem(text=route.display_name, icon=None, userData=route)

        self.route_btn.setCurrentIndex(target_idx)

        self.route_btn.currentIndexChanged.connect(self.on_choose_route)

    def update_route_table(self) -> None:
        """
        更新路线列表的显示
        :return:
        """
        if self.chosen_config is None:
            self.route_table.setRowCount(0)
            return

        # 统一使用白名单加载
        fake_config = WorldPatrolWhitelist('fake', is_mock=True)
        fake_config.type = WorldPatrolWhiteListType.WHITE.value.value
        fake_config.list = self.chosen_config.list

        route_list = self.ctx.world_patrol_route_data.load_all_route(whitelist=fake_config)
        route_cnt = len(route_list)
        self.route_table.setRowCount(route_cnt)

        for idx in range(route_cnt):
            route = route_list[idx]
            del_btn = ToolButton(FluentIcon.DELETE, parent=None)
            # 按钮的点击事件绑定route.unique_id
            del_btn.setProperty('route_id', route.unique_id)
            del_btn.clicked.connect(self.on_row_delete_clicked)

            self.route_table.setItem(idx, 0, QTableWidgetItem(route.display_name))
            self.route_table.setCellWidget(idx, 1, del_btn)

    def on_choose_existed(self, idx: int) -> None:
        self.chosen_config = self.existed_yml_btn.itemData(idx)

        self.update_display_by_config()

    def on_create_clicked(self) -> None:
        if self.chosen_config is not None:
            return

        self.chosen_config = create_new_whitelist()
        self.update_display_by_config()

    def on_delete_clicked(self):
        if self.chosen_config is None:
            return
        self.chosen_config.delete()

        self.chosen_config = None
        self.update_display_by_config()

    def on_cancel_clicked(self):
        self.chosen_config = None
        self.update_display_by_config()

    def on_choose_planet(self, idx: int) -> None:
        self.chosen_planet = self.planet_btn.itemData(idx)
        self.update_region_opt()
        self.update_route_opt()

    def on_choose_region(self, idx: int) -> None:
        self.chosen_region = self.region_btn.itemData(idx)
        self.update_route_opt()

    def on_choose_route(self, idx: int) -> None:
        self.chosen_route = self.route_btn.itemData(idx)

    def on_row_delete_clicked(self) -> None:
        """
        删除一条路线
        :return:
        """
        if self.chosen_config is None:
            return

        btn = self.sender()
        if btn is not None:
            # 获取点击按钮
            route_id = btn.property('route_id')

            current_list = self.chosen_config.list
            if route_id in current_list:
                current_list.remove(route_id)
                self.chosen_config.list = current_list

            row_idx = self.route_table.indexAt(btn.pos()).row()
            self.route_table.removeRow(row_idx)

    def on_add_planet_clicked(self) -> None:
        """
        添加整个星球的路线
        :return:
        """
        if self.chosen_config is None or self.chosen_planet is None:
            return

        route_list = self.ctx.world_patrol_route_data.load_all_route(target_planet=self.chosen_planet)
        current_list = self.chosen_config.list
        for route in route_list:
            if route.unique_id not in current_list:
                current_list.append(route.unique_id)

        self.chosen_config.list = current_list
        self.update_route_table()

    def on_add_region_clicked(self) -> None:
        """
        添加整个区域的路线
        :return:
        """
        if self.chosen_config is None or self.chosen_region is None:
            return

        route_list = self.ctx.world_patrol_route_data.load_all_route(target_region=self.chosen_region)
        current_list = self.chosen_config.list
        for route in route_list:
            if route.unique_id not in current_list:
                current_list.append(route.unique_id)

        self.chosen_config.list = current_list
        self.update_route_table()

    def on_add_route_clicked(self) -> None:
        """
        添加一条路线
        :return:
        """
        if self.chosen_config is None or self.chosen_route is None:
            return

        current_list = self.chosen_config.list
        if self.chosen_route.unique_id not in current_list:
            current_list.append(self.chosen_route.unique_id)

        self.chosen_config.list = current_list
        self.update_route_table()
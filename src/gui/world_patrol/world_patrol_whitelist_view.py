import base64
import os
from typing import List, Optional

import cv2
import flet as ft

from basic import os_utils
from basic.log_utils import log
from gui import components
from gui.sr_basic_view import SrBasicView
from gui.world_patrol import world_patrol_draft_route_view
from sr.app.world_patrol.world_patrol_route import WorldPatrolRouteId, WorldPatrolRoute, load_all_route_id
from sr.app.world_patrol.world_patrol_whitelist_config import WorldPatrolWhitelist, load_all_whitelist_id
from sr.const.map_const import PLANET_LIST, PLANET_2_REGION
from sr.context import Context


class WorldPatrolWhiteListView(components.Card, SrBasicView):

    def __init__(self, page: ft.Page, ctx: Context):
        SrBasicView.__init__(self, page, ctx)

        self.existed_list_dropdown = ft.Dropdown(
            label='编辑已有名单',
            on_change=self.on_existed_list_changed
        )
        self.cancel_edit_existed_btn = ft.ElevatedButton(text='取消编辑已有名单', on_click=self.clear_chosen_whitelist, disabled=True)
        self.save_list_btn = ft.ElevatedButton(text='保存', on_click=self.save_list, disabled=True)
        self.delete_list_btn = ft.ElevatedButton(text='删除', on_click=self.delete_list, disabled=True)

        self.existed_id_list: List[str] = []  # 名单列表
        whitelist_id_row = ft.Row(controls=[
            self.existed_list_dropdown,
            self.cancel_edit_existed_btn,
            self.save_list_btn,
            self.delete_list_btn,
        ])
        self.chosen_whitelist: Optional[WorldPatrolWhitelist] = None

        self.list_name_input = ft.TextField(label='名称', value='未命名')
        self.list_type_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option(text='白名单', key='white'),
                ft.dropdown.Option(text='黑名单', key='black'),
            ],
            label='类型', value='white')

        name_type_route = ft.Row(controls=[self.list_name_input, self.list_type_dropdown])

        self.planet_dropdown = ft.Dropdown(
            label='星球', width=100, options=[ft.dropdown.Option(text=p.cn, key=p.np_id) for p in PLANET_LIST],
            on_change=self.on_planet_changed
        )
        self.region_dropdown = ft.Dropdown(label='区域', width=200, on_change=self.on_region_change)
        self.existed_route_dropdown = ft.Dropdown(
            label='选择路线',
            on_change=self.on_existed_route_changed
        )

        self.add_planet_btn = ft.ElevatedButton(text='添加星球', disabled=True, on_click=self.on_add_planet_clicked)
        self.add_region_btn = ft.ElevatedButton(text='添加区域', disabled=True, on_click=self.on_add_region_clicked)
        self.add_route_btn = ft.ElevatedButton(text='添加路线', disabled=True, on_click=self.on_add_route_clicked)
        self.clear_list_btn = ft.ElevatedButton(text='清空', on_click=self.clear_selected_route, disabled=True)
        route_row = ft.Row(controls=[self.planet_dropdown, self.region_dropdown, self.existed_route_dropdown])
        btn_row = ft.Row(controls=[self.add_planet_btn, self.add_region_btn, self.add_route_btn, self.clear_list_btn])

        self.existed_route_id_list: List[WorldPatrolRouteId] = []  # 加载的所有列表
        self.selected_route_id_list: List[WorldPatrolRouteId] = []  # 选择进名单的列表

        self.image_width = 650
        self.map_img = ft.Image(src="a.png", fit=ft.ImageFit.CONTAIN, visible=False)

        self.display_route_list = ft.ListView(expand=1, spacing=10, auto_scroll=True)

        route_display_part = ft.Column(controls=[
            ft.Container(content=whitelist_id_row, padding=20),
            ft.Container(content=name_type_route, padding=20),
            ft.Container(content=route_row, padding=20),
            ft.Container(content=btn_row, padding=20),
            ft.Container(content=self.map_img, width=self.image_width, height=self.image_width,
                         alignment=ft.alignment.top_left)
        ], scroll=ft.ScrollMode.AUTO)

        content = ft.Row(controls=[
            route_display_part,
            ft.Container(content=self.display_route_list, padding=5, width=300)
        ])

        components.Card.__init__(self, content)

    def handle_after_show(self):
        self.load_whitelist_id_list()
        self.load_route_id_list()

    def load_whitelist_id_list(self):
        self.existed_id_list = load_all_whitelist_id()
        options = []
        for i in range(len(self.existed_id_list)):
            whitelist = WorldPatrolWhitelist(self.existed_id_list[i])
            opt = ft.dropdown.Option(text=whitelist.name, key=whitelist.id)
            options.append(opt)
        self.existed_list_dropdown.options = options
        self.existed_list_dropdown.value = None if self.chosen_whitelist is None else self.chosen_whitelist.id

    def on_existed_list_changed(self, e=None):
        self.chosen_whitelist = WorldPatrolWhitelist(self.existed_list_dropdown.value)
        self.list_name_input.value = self.chosen_whitelist.name
        self.list_type_dropdown.value = self.chosen_whitelist.type
        self.selected_route_id_list = []
        for unique_id in self.chosen_whitelist.list:
            for existed in self.existed_route_id_list:
                if unique_id == existed.unique_id:
                    self.selected_route_id_list.append(existed)
                    break

        self.update_display_route_list()
        self.update_component_disabled()
        self.update()

    def on_planet_changed(self, e):
        """
        选择星球后 更新区域列表 更新路线列表
        :param e:
        :return:
        """
        self.update_region_list_by_planet()
        self.load_route_id_list()
        self.update_component_disabled()

    def update_region_list_by_planet(self):
        """
        根据选择星球更新区域列表
        :return:
        """
        r_arr = PLANET_2_REGION[self.planet_dropdown.value] if self.planet_dropdown.value is not None else []
        self.region_dropdown.options = [ft.dropdown.Option(text=r.cn, key=r.pr_id) for r in r_arr if r.floor in [0, 1]]
        self.region_dropdown.value = None
        self.update()

    def on_region_change(self, e=None):
        """
        选择区域后 更新路线列表
        :return:
        """
        self.load_route_id_list()
        self.update_component_disabled()

    def clear_chosen_whitelist(self, e=None):
        """
        清空选择的名单
        :return:
        """
        self.chosen_whitelist = None
        self.existed_list_dropdown.value = None
        self.selected_route_id_list = []
        self.update_display_route_list()
        self.update_component_disabled()
        self.update()

    def clear_selected_route(self, e=None):
        """
        清空选择的路线
        :param e:
        :return:
        """
        self.selected_route_id_list = []
        self.update_display_route_list()
        self.update_component_disabled()

    def update_component_disabled(self):
        """
        统一更新各个组件的disabled
        :return:
        """
        list_chosen = self.chosen_whitelist is not None
        self.cancel_edit_existed_btn.disabled = not list_chosen
        self.delete_list_btn.disabled = not list_chosen
        self.save_list_btn.disabled = not list_chosen and len(self.selected_route_id_list) == 0
        self.clear_list_btn.disabled = len(self.selected_route_id_list) == 0

        self.add_planet_btn.disabled = self.planet_dropdown.value is None
        self.add_region_btn.disabled = self.region_dropdown.value is None
        self.add_route_btn.disabled = self.existed_route_dropdown.value is None

        self.update()

    def save_list(self, e):
        whitelist_id: Optional[str] = None
        if self.chosen_whitelist is None:
            existed_id_list = load_all_whitelist_id()
            for i in range(999):
                whitelist_id = self.list_type_dropdown.value + ('' if i == 0 else '_%02d' % i)
                if whitelist_id not in existed_id_list:
                    break
            self.chosen_whitelist = WorldPatrolWhitelist(whitelist_id)
        else:
            whitelist_id = self.existed_list_dropdown.value

        self.chosen_whitelist.name = self.list_name_input.value
        self.chosen_whitelist.type = self.list_type_dropdown.value
        self.chosen_whitelist.list = [i.unique_id for i in self.selected_route_id_list]
        log.info('保存成功')
        self.load_whitelist_id_list()
        self.existed_list_dropdown.value = whitelist_id
        self.update()
        self.on_existed_list_changed()

    def delete_list(self, e):
        """
        删除名单
        :param e:
        :return:
        """
        if self.chosen_whitelist is None:
            return
        file_path = os.path.join(os_utils.get_path_under_work_dir('config', 'world_patrol', 'whitelist'),
                                 '%s.yml' % self.chosen_whitelist.id)
        if not os.path.exists(file_path):
            return
        os.remove(file_path)
        self.clear_chosen_whitelist()
        self.load_whitelist_id_list()
        self.update()

    def get_yaml_str(self) -> str:
        """
        自己拼接yml文件内容
        :return:
        """
        content = ''

        content += "name: '%s'\n" % self.list_name_input.value
        content += "type: '%s'\n" % self.list_type_dropdown.value
        content += "list:\n"
        for i in self.selected_route_id_list:
            content += "  - '%s'\n" % i.unique_id

        return content

    def load_route_id_list(self):
        self.existed_route_id_list = load_all_route_id()
        chosen_value = None
        options = []
        for i in range(len(self.existed_route_id_list)):
            route: WorldPatrolRoute = WorldPatrolRoute(self.existed_route_id_list[i])
            if self.planet_dropdown.value is not None and route.tp.planet.np_id != self.planet_dropdown.value:
                continue
            if self.region_dropdown.value is not None and route.tp.region.pr_id != self.region_dropdown.value:
                continue
            opt = ft.dropdown.Option(text=self.existed_route_id_list[i].display_name, key=str(i))
            options.append(opt)
        self.existed_route_dropdown.options = options
        self.existed_route_dropdown.value = chosen_value
        self.update()

    def on_existed_route_changed(self, e=None):
        chosen_route_id: WorldPatrolRouteId = self.existed_route_id_list[int(self.existed_route_dropdown.value)]
        route: WorldPatrolRoute = WorldPatrolRoute(chosen_route_id)

        display_image = world_patrol_draft_route_view.draw_route_in_image(self.sr_ctx, route)
        # 图片转化成base64编码展示
        _, buffer = cv2.imencode('.png', display_image)
        base64_data = base64.b64encode(buffer)
        base64_string = base64_data.decode("utf-8")
        self.map_img.visible = True
        self.map_img.src_base64 = base64_string

        self.update_component_disabled()

    def on_add_planet_clicked(self, e):
        """
        添加整个星球
        :param e:
        :return:
        """
        if self.planet_dropdown.value is None:
            return
        for i in range(len(self.existed_route_id_list)):
            route: WorldPatrolRoute = WorldPatrolRoute(self.existed_route_id_list[i])
            if self.planet_dropdown.value is not None and route.tp.planet.np_id != self.planet_dropdown.value:
                continue
            self.add_route_to_selected(self.existed_route_id_list[i])

    def on_add_region_clicked(self, e):
        """
        添加整个区域
        :param e:
        :return:
        """
        if self.planet_dropdown.value is None:
            return
        for i in range(len(self.existed_route_id_list)):
            route: WorldPatrolRoute = WorldPatrolRoute(self.existed_route_id_list[i])
            if self.planet_dropdown.value is not None and route.tp.planet.np_id != self.planet_dropdown.value:
                continue
            if self.region_dropdown.value is not None and route.tp.region.pr_id != self.region_dropdown.value:
                continue
            self.add_route_to_selected(self.existed_route_id_list[i])

    def on_add_route_clicked(self, e):
        """
        添加单条路线
        :param e:
        :return:
        """
        chosen: WorldPatrolRouteId = self.existed_route_id_list[int(self.existed_route_dropdown.value)]
        self.add_route_to_selected(chosen)

    def add_route_to_selected(self, to_add: WorldPatrolRouteId):
        """
        添加路线到选择列表中
        :param to_add:
        :return:
        """
        existed: bool = False
        for route_id in self.selected_route_id_list:
            if to_add.unique_id == route_id.unique_id:
                existed = True
                break

        if not existed:
            self.selected_route_id_list.append(to_add)
            self.update_display_route_list()
            self.update_component_disabled()

    def update_display_route_list(self):
        route_text_list = []
        for route_id in self.selected_route_id_list:
            route_text_list.append(
                ft.Row(controls=[
                    ft.TextButton(text=route_id.display_name, on_click=self.on_list_route_selected, width=250),
                    ft.IconButton(icon=ft.icons.DELETE_FOREVER_ROUNDED, tooltip="删除", data=route_id.unique_id, on_click=self.on_delete_route)
                ])
            )

        self.display_route_list.controls = route_text_list
        self.update()

    def on_list_route_selected(self, e):
        for i in range(len(self.existed_route_id_list)):
            if self.existed_route_id_list[i].display_name == e.control.text:
                self.existed_route_dropdown.value = str(i)
        self.on_existed_route_changed()

    def on_delete_route(self, e):
        idx: int = -1
        for i in range(len(self.selected_route_id_list)):
            if e.control.data == self.selected_route_id_list[i].unique_id:
                idx = i
                break
        if idx != -1:
            self.selected_route_id_list.pop(idx)
            self.update_display_route_list()


_world_patrol_white_list_view: Optional[WorldPatrolWhiteListView] = None


def get(page: ft.Page, ctx: Context) -> WorldPatrolWhiteListView:
    global _world_patrol_white_list_view
    if _world_patrol_white_list_view is None:
        _world_patrol_white_list_view = WorldPatrolWhiteListView(page, ctx)

    return _world_patrol_white_list_view

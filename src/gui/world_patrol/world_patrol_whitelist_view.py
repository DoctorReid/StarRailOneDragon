import base64
import os
from typing import List

import cv2
import flet as ft

from basic import os_utils
from basic.log_utils import log
from gui import components
from gui.world_patrol import world_patrol_draft_route_view
from sr.app.world_patrol import WorldPatrolRouteId, WorldPatrolRoute, WorldPatrolWhitelist, load_all_route_id, \
    load_all_whitelist_id
from sr.context import Context


class WorldPatrolWhiteListView(components.Card):

    def __init__(self, page: ft.Page, ctx: Context):
        self.page: ft.Page = page
        self.ctx: Context = ctx

        self.existed_list_dropdown = ft.Dropdown(
            label='编辑已有名单',
            on_change=self.on_existed_list_changed
        )
        self.cancel_edit_existed = ft.ElevatedButton(text='取消编辑已有名单', on_click=self.cancel_edit_existed)
        self.save_list_btn = ft.ElevatedButton(text='保存', on_click=self.save_list)
        self.existed_id_list: List[str] = []  # 名单列表
        whitelist_id_row = ft.Row(controls=[
            self.existed_list_dropdown,
            self.cancel_edit_existed,
            self.save_list_btn
        ])
        self.chosen_whitelist: WorldPatrolWhitelist = None

        self.load_whitelist_id_list()

        self.list_type_radio = ft.RadioGroup(content=ft.Column([
            ft.Radio(value="white", label="白名单"),
            ft.Radio(value="black", label="黑名单"),
        ]), value='white')

        self.existed_route_dropdown = ft.Dropdown(
            label='选择路线',
            on_change=self.on_existed_route_changed
        )
        self.add_route_btn = ft.ElevatedButton(text='添加到名单', disabled=True, on_click=self.on_add_clicked)
        route_row = ft.Row(controls=[self.existed_route_dropdown, self.add_route_btn])

        self.existed_route_id_list: List[WorldPatrolRouteId] = []  # 加载的所有列表
        self.selected_route_id_list: List[WorldPatrolRouteId] = []  # 选择进名单的列表

        self.image_width = 1000
        self.map_img = ft.Image(src="a.png", fit=ft.ImageFit.CONTAIN, visible=False)

        self.load_route_id_list()

        self.display_route_list = ft.ListView(expand=1, spacing=10, padding=20, auto_scroll=True)

        route_display_part = ft.Column(controls=[
            ft.Container(content=whitelist_id_row, padding=20),
            ft.Container(content=self.list_type_radio, padding=20),
            ft.Container(content=route_row, padding=20),
            ft.Container(content=self.map_img, width=self.image_width, height=self.image_width,
                         alignment=ft.alignment.top_left)
        ])

        content = ft.Row(controls=[
            route_display_part,
            ft.Container(content=self.display_route_list, padding=5, width=400)
        ])

        super().__init__(content)

    def load_whitelist_id_list(self):
        self.existed_id_list = load_all_whitelist_id()
        options = []
        for i in range(len(self.existed_id_list)):
            opt = ft.dropdown.Option(text=self.existed_id_list[i], key=self.existed_id_list[i])
            options.append(opt)
        self.existed_list_dropdown.options = options

    def on_existed_list_changed(self, e):
        self.chosen_whitelist = WorldPatrolWhitelist(self.existed_list_dropdown.value)
        self.list_type_radio.value = self.chosen_whitelist.type
        self.selected_route_id_list = []
        for unique_id in self.chosen_whitelist.list:
            for existed in self.existed_route_id_list:
                if unique_id == existed.unique_id:
                    self.selected_route_id_list.append(existed)
                    break
        self.update_display_route_list()

    def cancel_edit_existed(self, e):
        self.existed_list_dropdown.value = None
        self.selected_route_id_list = []
        self.update_display_route_list()

    def save_list(self, e):
        whitelist_id: str
        if self.existed_list_dropdown.value is None:
            existed_id_list = load_all_whitelist_id()
            for i in range(999):
                whitelist_id = self.list_type_radio.value + ('' if i == 0 else '_%02d' % i)
                if whitelist_id not in existed_id_list:
                    break
        else:
            whitelist_id = self.existed_list_dropdown.value

        file_path = os.path.join(os_utils.get_path_under_work_dir('config', 'world_patrol', 'whitelist'), '%s.yml' % whitelist_id)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(self.get_yaml_str())
        log.info('保存成功 %s', file_path)

    def get_yaml_str(self) -> str:
        """
        自己拼接yml文件内容
        :return:
        """
        content = ''

        content += "type: '%s'\n" % self.list_type_radio.value
        content += "list:\n"
        for i in self.selected_route_id_list:
            content += "  - '%s'\n" % i.unique_id

        return content

    def load_route_id_list(self):
        self.existed_route_id_list = load_all_route_id()
        chosen_value = None
        options = []
        for i in range(len(self.existed_route_id_list)):
            opt = ft.dropdown.Option(text=self.existed_route_id_list[i].display_name, key=str(i))
            options.append(opt)
        self.existed_route_dropdown.options = options
        self.existed_route_dropdown.value = chosen_value

    def on_existed_route_changed(self, e=None):
        chosen_route_id: WorldPatrolRouteId = self.existed_route_id_list[int(self.existed_route_dropdown.value)]
        route: WorldPatrolRoute = WorldPatrolRoute(chosen_route_id)

        display_image = world_patrol_draft_route_view.draw_route_in_image(self.ctx, route)
        # 图片转化成base64编码展示
        _, buffer = cv2.imencode('.png', display_image)
        base64_data = base64.b64encode(buffer)
        base64_string = base64_data.decode("utf-8")
        self.map_img.visible = True
        self.map_img.src_base64 = base64_string

        self.add_route_btn.disabled = False
        self.page.update()

    def on_add_clicked(self, e):
        chosen: WorldPatrolRouteId = self.existed_route_id_list[int(self.existed_route_dropdown.value)]
        existed: bool = False
        for route_id in self.selected_route_id_list:
            if chosen.unique_id == route_id.unique_id:
                existed = True
                break

        if not existed:
            self.selected_route_id_list.append(chosen)
        self.update_display_route_list()

    def update_display_route_list(self):
        route_text_list = []
        for route_id in self.selected_route_id_list:
            route_text_list.append(
                ft.Row(controls=[
                    ft.TextButton(text=route_id.display_name, on_click=self.on_list_route_selected),
                    ft.IconButton(icon=ft.icons.DELETE_FOREVER_ROUNDED, tooltip="删除", data=route_id.unique_id, on_click=self.on_delete_route)
                ])
            )

        self.display_route_list.controls = route_text_list
        self.page.update()

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


gv: WorldPatrolWhiteListView = None


def get(page: ft.Page, ctx: Context) -> WorldPatrolWhiteListView:
    global gv
    if gv is None:
        gv = WorldPatrolWhiteListView(page, ctx)

    return gv

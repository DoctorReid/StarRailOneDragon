import base64
from typing import List, Optional, Callable

import cv2
import flet as ft

from basic.i18_utils import gt
from gui import components
from sr.const.character_const import CHARACTER_PATH_LIST, CHARACTER_COMBAT_TYPE_LIST, filter_character_list, Character
from sr.image.image_holder import ImageHolder


class CharacterAvatar(ft.Container):

    def __init__(self, ih: ImageHolder,
                 c: Character,
                 is_chosen: bool = False,
                 on_click: Optional[Callable] = None):
        avatar_image = ih.get_character_avatar_template(c.id)
        _, buffer = cv2.imencode('.png', avatar_image.origin)
        base64_data = base64.b64encode(buffer)
        base64_string = base64_data.decode("utf-8")

        self.check = ft.Icon(name=ft.icons.CHECK_CIRCLE, visible=is_chosen, size=20)

        self.stack = ft.Stack(width=90, height=90,
                              controls=[
                                  ft.Image(src_base64=base64_string, width=90, height=90),
                                  ft.Container(content=self.check, alignment=ft.alignment.bottom_right),
                              ],
                              )
        ft.Container.__init__(self, content=self.stack, on_click=on_click, data=c.id)

    def update_chosen(self, is_chosen: bool):
        """
        是否被选择
        :param is_chosen:
        :return:
        """
        self.check.visible = is_chosen
        if self.page is not None:
            self.update()


class CharacterInput(components.Card):

    def __init__(self,
                 ih: ImageHolder,
                 max_chosen_num: int = 1,
                 chosen_list: List[id] = None,
                 on_value_changed: Optional[Callable] = None):
        self.ih: ImageHolder = ih

        self.name_input = ft.TextField(label=gt('名称', 'ui'), width=120, on_change=self._update_avatar_grid)

        self.destiny_input = ft.Dropdown(
            label=gt('命途', 'ui'), width=120,
            options=[ft.dropdown.Option(key=i.id, text=gt(i.cn, 'ui')) for i in CHARACTER_PATH_LIST],
            on_change=self._update_avatar_grid
        )
        self.destiny_input.options.insert(0, ft.dropdown.Option(key='all', text=gt('全部', 'ui')))
        self.destiny_input.value = 'all'

        self.combat_type_input = ft.Dropdown(
            label=gt('属性', 'ui'), width=120,
            options=[ft.dropdown.Option(key=i.id, text=gt(i.cn, 'ui')) for i in CHARACTER_COMBAT_TYPE_LIST],
            on_change=self._update_avatar_grid
        )
        self.combat_type_input.options.insert(0, ft.dropdown.Option(key='all', text=gt('全部', 'ui')))
        self.combat_type_input.value = 'all'

        self.level_input = ft.Dropdown(
            label=gt('星级', 'ui'), width=120,
            options=[
                ft.dropdown.Option(key='all', text=gt('全部', 'ui')),
                ft.dropdown.Option(key='5', text='5'),
                ft.dropdown.Option(key='4', text='4')
            ],
            value='all', on_change=self._update_avatar_grid
        )

        self.character_image_map: dict[str, CharacterAvatar] = {}
        avatar_grid = ft.GridView(controls=[], max_extent=90, runs_count=4)
        for c in filter_character_list():
            avatar = CharacterAvatar(self.ih, c, on_click=self._on_avatar_click)
            self.character_image_map[c.id] = avatar
            avatar_grid.controls.append(avatar)

        self.title = components.CardTitleText(title=gt('选择角色', 'ui'))
        content = ft.Column(controls=[
            ft.Row(controls=[self.name_input, self.destiny_input, self.combat_type_input, self.level_input]),
            avatar_grid
        ])

        components.Card.__init__(self, content, self.title)

        self.max_chosen_num: int = max_chosen_num
        self.chosen_list: List[str] = []
        self.update_chosen_list(chosen_list)

        self.value_changed_callback: Optional[Callable] = on_value_changed

    def _update_avatar_grid(self, e):
        to_show_list = filter_character_list(
            destiny_id=self.destiny_input.value if self.destiny_input.value is not None and self.destiny_input.value != 'all' else None,
            combat_type_id=self.combat_type_input.value if self.combat_type_input.value is not None and self.combat_type_input.value != 'all' else None,
            level=int(self.level_input.value) if self.level_input.value is not None and self.level_input.value != 'all' else None,
            character_name=self.name_input.value if self.name_input.value is not None and self.name_input.value != '' else None,
        )

        for c_id, component in self.character_image_map.items():
            component.visible = False

        for c in to_show_list:
            self.character_image_map[c.id].visible = True

        if self.page is not None:
            self.update()

    def update_title(self, title: str):
        self.title.update_title(title)
        self.title.update()

    def update_value_changed_callback(self, callback: Callable):
        self.value_changed_callback = callback

    def update_chosen_list(self, chosen_list: List[str]):
        """
        更新选中的列表
        列表长度超出限定数量时，只保留前N个
        :param chosen_list: 选择的角色列表
        :return:
        """
        self.chosen_list.clear()

        if chosen_list is not None:
            for i in chosen_list:
                if len(self.chosen_list) < self.max_chosen_num:
                    self.chosen_list.append(i)
        self._update_chosen_list_display()

    def _update_chosen_list_display(self):
        """
        按选中的名单更新显示
        :return:
        """
        for c_id, component in self.character_image_map.items():
            component.update_chosen(False)

        for c_id in self.chosen_list:
            if c_id == 'none':
                continue
            self.character_image_map[c_id].update_chosen(True)

    def _on_avatar_click(self, e):
        """
        点击头像时 更新选中的显示
        :param e:
        :return:
        """
        c_id = e.control.data
        add: bool = c_id not in self.chosen_list  # 是否添加
        if not add:
            self.chosen_list.remove(c_id)
            self._update_chosen_list_display()
            self._on_value_changed()
        elif len(self.chosen_list) == self.max_chosen_num:
            if self.max_chosen_num > 1:
                # 可选多个的情况 通常是选择配队的时候 选满了就不能再选了
                return
            else:
                # 只选一个的情况 通常是选支援角色的时候 这时候重新点就换一个 优化使用体验
                self.chosen_list[0] = c_id
                self._update_chosen_list_display()
                self._on_value_changed()
        else:
            self.chosen_list.append(c_id)
            self._update_chosen_list_display()
            self._on_value_changed()

    def _on_value_changed(self):
        """
        选中值改变时 触发的事件回调
        :return:
        """
        if self.value_changed_callback is None:
            return
        self.value_changed_callback(self.chosen_list)

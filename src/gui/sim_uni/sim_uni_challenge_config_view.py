from typing import Optional, List, Callable

import flet as ft
from flet_core import ControlEvent

from basic.i18_utils import gt
from basic.log_utils import log
from gui.components import RectOutlinedButton, SettingsListItem, SettingsList, Card, CardTitleText, \
    SettingsListGroupTitle
from gui.settings import gui_config
from gui.settings.gui_config import ThemeColors
from gui.sr_basic_view import SrBasicView
from sr.sim_uni.sim_uni_challenge_config import SimUniChallengeConfig
from sr.context.context import Context
from sr.sim_uni.sim_uni_const import SimUniLevelTypeEnum, SimUniLevelType, level_type_from_id, level_type_from_name, \
    SimUniPath, SimUniBlessLevel, SimUniBlessEnum, bless_enum_from_title, SimUniCurioEnum, \
    curio_enum_from_name


class Option:

    def __init__(self, uid: str, name: str):
        self.uid: str = uid
        self.name: str = name


class OptionCheckList(SettingsList):

    def __init__(self, options: List[Option],
                 header_list: Optional[List[SettingsListItem]] = None,
                 on_change: Optional[Callable[[List[str]], None]] = None
                 ):
        self.check_map: dict[str, ft.Checkbox] = {}
        self.item_map: dict[str, SettingsListItem] = {}

        option_items = []
        if header_list is not None:
            for header_item in header_list:
                option_items.append(header_item)
        for opt in options:
            check = ft.Checkbox(data=opt.uid, on_change=self._on_checked)
            self.check_map[opt.uid] = check
            item = SettingsListItem(gt(opt.name, 'ui'), check)
            self.item_map[opt.uid] = item
            option_items.append(item)

        SettingsList.__init__(self, option_items)

        self.chosen_id_list: List[str] = []
        self.on_change: Optional[Callable[[List[str]], None]] = on_change

    def _on_checked(self, e: ControlEvent):
        """
        选项勾选
        :param e:
        :return:
        """
        uid = e.control.data
        check = e.control.value

        if check and uid not in self.chosen_id_list:
            self.chosen_id_list.append(uid)
        elif not check and uid in self.chosen_id_list:
            self.chosen_id_list.remove(uid)

        if self.on_change is not None:
            self.on_change(self.chosen_id_list)

    def set_chosen_list(self, new_list: List[str]):
        """
        更新选项勾选情况
        :param new_list:
        :return:
        """
        self.chosen_id_list = new_list
        for type_id, check in self.check_map.items():
            check.value = type_id in self.chosen_id_list
            check.update()

    def update_shown(self, show_id_list: List[str]):
        """
        根据ID显示
        :param show_id_list:
        :return:
        """
        for uid, item in self.item_map.items():
            item.visible = uid in show_id_list
            item.update()


class BlessSelectionCard(Card):

    def __init__(self, on_change: Optional[Callable[[List[str]], None]] = None):
        title = CardTitleText(gt('祝福', 'ui'))

        self.path_dropdown = ft.Dropdown(
            label=gt('命途', 'ui'),
            width=100,
            options=[ft.dropdown.Option(
                key=path.name, text=gt(path.value, 'ui')
            ) for path in SimUniPath],
            on_change=self._update_bless_list_shown
        )

        self.level_dropdown = ft.Dropdown(
            label=gt('祝福等级', 'ui'),
            width=100,
            options=[ft.dropdown.Option(key=level.name, text=gt(level.value, 'ui')) for level in SimUniBlessLevel],
            on_change=self._update_bless_list_shown
        )

        header_item_list = [SettingsListItem('', ft.Row(controls=[self.path_dropdown, self.level_dropdown]))]
        options = [Option(bless.name, bless.value.title) for bless in SimUniBlessEnum]
        self.options_list = OptionCheckList(options, header_list=header_item_list, on_change=on_change)

        Card.__init__(self, content=self.options_list, title=title, width=400)

    def set_chosen_list(self, new_list: List[str]):
        self.options_list.set_chosen_list(new_list)

    def _update_bless_list_shown(self, e=None):
        """
        更新祝福列表的显示
        :return:
        """
        show_id_list: List[str] = []
        path_id = self.path_dropdown.value
        bless_level_id = self.level_dropdown.value
        for bless in SimUniBlessEnum:
            if path_id is not None and bless.value.path.name != path_id:
                continue
            if bless_level_id is not None and bless.value.level.name != bless_level_id:
                continue
            show_id_list.append(bless.name)

        self.options_list.update_shown(show_id_list)


class LevelTypeSelectionCard(Card):

    def __init__(self, on_change: Optional[Callable[[List[str]], None]] = None):
        title = CardTitleText(gt('楼层类型', 'ui'))

        self.check_map: dict[str, ft.Checkbox] = {}

        options = [Option(level_type.value.type_id, level_type.value.type_name) for level_type in SimUniLevelTypeEnum]
        self.options_list = OptionCheckList(options, on_change=on_change)

        Card.__init__(self, content=self.options_list, title=title, width=300)

        self.chosen_id_list: List[str] = []
        self.on_change: Optional[Callable[[List[str]], None]] = on_change

    def set_chosen_list(self, new_list: List[str]):
        self.options_list.set_chosen_list(new_list)


class CurioSelectionCard(Card):

    def __init__(self, on_change: Optional[Callable[[List[str]], None]] = None):
        title = CardTitleText(gt('奇物', 'ui'))
        self.curio_text = ft.TextField(hint_text=gt('名称或拼音首字母', 'ui'), height=50,
                                       on_change=self._update_curio_list_shown)

        header_item_list = [SettingsListItem('奇物搜索', self.curio_text)]
        options = [Option(curio.name, curio.value.name) for curio in SimUniCurioEnum]
        self.options_list = OptionCheckList(options, header_list=header_item_list, on_change=on_change)

        Card.__init__(self, content=self.options_list, title=title, width=400)

    def set_chosen_list(self, new_list: List[str]):
        self.options_list.set_chosen_list(new_list)

    def _update_curio_list_shown(self, e=None):
        """
        更新奇物列表的显示
        :return:
        """
        show_id_list: List[str] = []
        text = self.curio_text.value
        for curio in SimUniCurioEnum:
            if text is None or len(text) == 0:
                show_id_list.append(curio.name)
            elif gt(curio.value.name, 'ui').find(text) > -1:
                show_id_list.append(curio.name)
            elif curio.value.py.find(text) > -1:
                show_id_list.append(curio.name)

        self.options_list.update_shown(show_id_list)


class SimUniChallengeConfigView(ft.Row, SrBasicView):

    def __init__(self, page: ft.Page, ctx: Context):
        SrBasicView.__init__(self, page, ctx)
        theme: ThemeColors = gui_config.theme()

        self.existed_dropdown = ft.Dropdown(width=200, height=55, on_change=self._on_chosen_changed)
        self.existed_config_list: Optional[List[SimUniChallengeConfig]] = None
        self.chosen_config: Optional[SimUniChallengeConfig] = None

        self.new_btn = RectOutlinedButton(text=gt('新建', 'ui'), on_click=self._on_new_clicked)
        self.copy_btn = RectOutlinedButton(text=gt('复制', 'ui'), disabled=True, on_click=self._on_copy_clicked)
        self.del_btn = RectOutlinedButton(text=gt('删除', 'ui'), disabled=True, on_click=self._on_del_clicked)
        op_btn_row = ft.Row(controls=[self.new_btn, self.copy_btn, self.del_btn])

        self.name_text = ft.TextField(disabled=True, height=50, on_change=self._on_name_changed)

        self.path_dropdown = ft.Dropdown(options=[
            ft.dropdown.Option(key=path.name, text=gt(path.value, 'ui')) for path in SimUniPath
        ], disabled=True, height=55, on_change=self._on_path_changed)

        self.bless_btn = RectOutlinedButton(text=gt('编辑', 'ui'), disabled=True,
                                            on_click=self._on_bless_edit_clicked)
        self.bless_text = ft.TextField(disabled=True, min_lines=3, max_lines=7, width=380, multiline=True,
                                       on_blur=self._on_bless_text_update)

        self.bless_btn_2 = RectOutlinedButton(text=gt('编辑', 'ui'), disabled=True,
                                              on_click=self._on_bless_edit_2_clicked)
        self.bless_text_2 = ft.TextField(disabled=True, min_lines=3, max_lines=7, width=380, multiline=True,
                                         on_blur=self._on_bless_text_2_update)

        self.level_type_btn = RectOutlinedButton(text=gt('编辑', 'ui'), disabled=True,
                                                 on_click=self._on_level_type_edit_clicked)
        self.level_type_text = ft.TextField(disabled=True, min_lines=3, max_lines=7, width=380, multiline=True,
                                            on_blur=self._on_level_type_text_update)

        self.curio_btn = RectOutlinedButton(text=gt('编辑', 'ui'), disabled=True,
                                            on_click=self._on_curio_edit_clicked)
        self.curio_text = ft.TextField(disabled=True, min_lines=3, max_lines=7, width=380, multiline=True,
                                       on_blur=self._on_curio_text_update)

        self.skip_herta_checkbox = ft.Checkbox(disabled=True, on_change=self._on_skip_herta_changed)
        self.technique_fight_checkbox = ft.Checkbox(disabled=True, on_change=self._on_technique_fight_changed)
        self.technique_only_checkbox = ft.Checkbox(disabled=True, on_change=self._on_technique_only_changed)
        self.max_consumable_cnt = ft.Dropdown(options=[ft.dropdown.Option(key=str(i), text=str(i)) for i in range(6)],
                                              on_change=self._on_max_consumable_cnt_changed, width=100)

        config_list = SettingsList(controls=[
            SettingsListItem(gt('选择配置', 'ui'), self.existed_dropdown),
            SettingsListItem('', op_btn_row),
            SettingsListItem(gt('配置名称', 'ui'), self.name_text),
            SettingsListItem(gt('命途', 'ui'), self.path_dropdown),
            SettingsListGroupTitle(gt('优先级', 'ui')),
            SettingsListItem(gt('祝福第一优先级', 'ui'), self.bless_btn),
            SettingsListItem('', self.bless_text),
            SettingsListItem(gt('祝福第二优先级', 'ui'), self.bless_btn_2),
            SettingsListItem('', self.bless_text_2),
            SettingsListItem(gt('楼层优先级', 'ui'), self.level_type_btn),
            SettingsListItem('', self.level_type_text),
            SettingsListItem(gt('奇物优先级', 'ui'), self.curio_btn),
            SettingsListItem('', self.curio_text),
            SettingsListGroupTitle(gt('战斗', 'ui')),
            SettingsListItem(gt('跳过黑塔', 'ui'), self.skip_herta_checkbox),
            SettingsListItem(gt('秘技开怪', 'ui'), self.technique_fight_checkbox),
            SettingsListItem(gt('仅秘技开怪', 'ui'), self.technique_only_checkbox),
            SettingsListItem(gt('单次最多消耗品个数', 'ui'), self.max_consumable_cnt),

        ], width=400)
        config_card = Card(config_list)

        self.bless_card = BlessSelectionCard(on_change=self._on_bless_priority_changed)
        self.bless_card.visible = False

        self.bless_card_2 = BlessSelectionCard(on_change=self._on_bless_priority_2_changed)
        self.bless_card_2.visible = False

        self.level_type_card = LevelTypeSelectionCard(on_change=self._on_level_type_priority_changed)
        self.level_type_card.visible = False

        self.curio_card = CurioSelectionCard(on_change=self._on_curio_priority_changed)
        self.curio_card.visible = False

        ft.Row.__init__(self, controls=[config_card, self.level_type_card, self.bless_card, self.bless_card_2, self.curio_card])

    def handle_after_show(self):
        self._load_existed_config_list()

    def _load_existed_config_list(self):
        """
        加载现有配置
        :return:
        """
        self.existed_config_list = self.sr_ctx.sim_uni_challenge_all_config.load_all_challenge_config()
        self.existed_dropdown.options = [
            ft.dropdown.Option(key=str(config.idx), text=gt(config.name, 'ui')) for config in self.existed_config_list
        ]
        self.existed_dropdown.update()

    def _on_chosen_changed(self, e=None):
        """
        选择的配置文件变更
        :param e:
        :return:
        """
        self.chosen_config = None
        if self.existed_dropdown.value is None:
            return
        for config in self.existed_config_list:
            if str(config.idx) == self.existed_dropdown.value:
                self.chosen_config = config
                break
        self._update_config_card_status()
        self._load_config_to_input()

    def _update_config_card_status(self):
        """
        更新左边的行
        :return:
        """
        config_chosen = self.chosen_config is not None

        self.copy_btn.disabled = not config_chosen

        self.del_btn.disabled = not config_chosen

        self.name_text.disabled = not config_chosen

        self.path_dropdown.disabled = not config_chosen

        self.bless_btn.disabled = not config_chosen

        self.bless_btn_2.disabled = not config_chosen

        self.level_type_btn.disabled = not config_chosen

        self.curio_btn.disabled = not config_chosen

        self.skip_herta_checkbox.disabled = not config_chosen

        self.technique_fight_checkbox.disabled = not config_chosen

        self.technique_only_checkbox.disabled = not config_chosen

        self.max_consumable_cnt.disabled = not config_chosen

        self.update()

    def _load_config_to_input(self):
        """
        将各个配置显示到输入框中
        :return:
        """
        self.name_text.value = '' if self.chosen_config is None else self.chosen_config.name
        self.name_text.update()

        self.path_dropdown.value = None if self.chosen_config is None else self.chosen_config.path
        self.path_dropdown.update()

        self._update_bless_text()
        self._update_bless_text_2()
        self._update_level_type_text()
        self._update_curio_text()

        self.skip_herta_checkbox.value = self.chosen_config.skip_herta
        self.technique_fight_checkbox.value = self.chosen_config.technique_fight
        self.technique_only_checkbox.value = self.chosen_config.technique_only
        self.max_consumable_cnt.value = str(self.chosen_config.max_consumable_cnt)

        self.update()

    def _on_existed_list_changed(self, chosen_idx: Optional[int]):
        """
        新建、复制、删除导致的列表变动
        :return:
        """
        self._load_existed_config_list()
        self.existed_dropdown.value = None if chosen_idx is None else str(chosen_idx)
        self.existed_dropdown.update()
        self._on_chosen_changed()

    def _on_new_clicked(self, e):
        """
        点击新建
        :param e:
        :return:
        """
        chosen_config = self.sr_ctx.sim_uni_challenge_all_config.create_new_challenge_config()
        self._on_existed_list_changed(chosen_config.idx)

    def _on_copy_clicked(self, e):
        """
        复制
        :param e:
        :return:
        """
        chosen_config = self.sr_ctx.sim_uni_challenge_all_config.create_new_challenge_config(self.chosen_config.idx)
        chosen_config.name = chosen_config.name + ' - copy'
        self._on_existed_list_changed(chosen_config.idx)

    def _on_del_clicked(self, e):
        """
        删除
        :param e:
        :return:
        """
        self.chosen_config.delete()
        self._on_existed_list_changed(None)

    def _on_name_changed(self, e):
        """
        配置名称改变
        :param e:
        :return:
        """
        self.chosen_config.name = self.name_text.value

    def _on_path_changed(self, e):
        """
        选择命途改变
        :return:
        """
        self.chosen_config.path = self.path_dropdown.value

    def _update_priority_status(self, card: Card, text: ft.TextField):
        """
        显示特定的选项
        :param card:
        :return:
        """
        self.level_type_card.visible = False
        self.level_type_card.update()

        self.level_type_text.disabled = True
        self.level_type_text.update()

        self.bless_card.visible = False
        self.bless_card.update()

        self.bless_text.disabled = True
        self.bless_text.update()

        self.bless_card_2.visible = False
        self.bless_card_2.update()

        self.bless_text_2.disabled = True
        self.bless_text_2.update()

        self.curio_card.visible = False
        self.curio_card.update()

        self.curio_text.disabled = True
        self.curio_text.update()

        card.visible = True
        card.update()

        text.disabled = False
        text.update()

    def _on_bless_edit_clicked(self, e):
        """
        编辑祝福优先级 - 第一优先级
        :param e:
        :return:
        """
        self._update_priority_status(self.bless_card, self.bless_text)
        self.bless_card.set_chosen_list(self.chosen_config.bless_priority)

    def _on_bless_priority_changed(self, new_list: List[str]):
        """
        祝福优先级改变 - 第一优先级
        :return:
        """
        self.chosen_config.bless_priority = new_list
        self._update_bless_text()

    def _update_bless_text(self):
        """
        更新祝福优先级的文本 - 第一优先级
        :return:
        """
        bless_list: List[SimUniBlessEnum] = []
        if self.chosen_config is not None:
            for bless_id in self.chosen_config.bless_priority:
                bless_list.append(SimUniBlessEnum[bless_id])

        text: str = ''
        for bless in bless_list:
            text += gt(bless.value.title, 'ui') + '\n'

        self.bless_text.value = text
        self.bless_text.update()

    def _on_bless_text_update(self, e):
        """
        祝福优先级的文本框输出改变 - 第一优先级
        :param e:
        :return:
        """
        bless_name_list = self.get_str_list(self.bless_text)
        bless_list: List[SimUniBlessEnum] = []
        for bless_name in bless_name_list:
            bless_enum = bless_enum_from_title(bless_name)
            if bless_enum is None:
                log.error('文本输入非法 %s 本次改动不保存', bless_name)
                return  # 有一个错误就不继续了
            bless_list.append(bless_enum)

        bless_id_list = [bless.name for bless in bless_list]
        self.chosen_config.bless_priority = bless_id_list

    def _on_bless_edit_2_clicked(self, e):
        """
        编辑祝福优先级 - 第二优先级
        :param e:
        :return:
        """
        self._update_priority_status(self.bless_card_2, self.bless_text_2)
        self.bless_card_2.set_chosen_list(self.chosen_config.bless_priority_2)

    def _on_bless_priority_2_changed(self, new_list: List[str]):
        """
        祝福优先级改变 - 第二优先级
        :return:
        """
        self.chosen_config.bless_priority_2 = new_list
        self._update_bless_text_2()

    def _update_bless_text_2(self):
        """
        更新祝福优先级的文本 - 第二优先级
        :return:
        """
        bless_list: List[SimUniBlessEnum] = []
        if self.chosen_config is not None:
            for bless_id in self.chosen_config.bless_priority_2:
                bless_list.append(SimUniBlessEnum[bless_id])

        text: str = ''
        for bless in bless_list:
            text += gt(bless.value.title, 'ui') + '\n'

        self.bless_text_2.value = text
        self.bless_text_2.update()

    def _on_bless_text_2_update(self, e):
        """
        祝福优先级的文本框输出改变 - 第二优先级
        :param e:
        :return:
        """
        bless_name_list = self.get_str_list(self.bless_text_2)
        bless_list: List[SimUniBlessEnum] = []
        for bless_name in bless_name_list:
            bless_enum = bless_enum_from_title(bless_name)
            if bless_enum is None:
                log.error('文本输入非法 %s 本次改动不保存', bless_name)
                return  # 有一个错误就不继续了
            bless_list.append(bless_enum)

        bless_id_list = [bless.name for bless in bless_list]
        self.chosen_config.bless_priority_2 = bless_id_list

    def _on_level_type_edit_clicked(self, e):
        """
        编辑楼层优先级
        :param e:
        :return:
        """
        self.level_type_card.set_chosen_list(self.chosen_config.level_type_priority)
        self._update_priority_status(self.level_type_card, self.level_type_text)

    def _on_level_type_priority_changed(self, new_list: List[str]):
        """
        :param new_list:
        :return:
        """
        self.chosen_config.level_type_priority = new_list
        self._update_level_type_text()

    def _update_level_type_text(self):
        """
        更新楼层优先级的文本
        :return:
        """
        level_type_list: List[SimUniLevelType] = []
        if self.chosen_config is not None:
            for level_type_id in self.chosen_config.level_type_priority:
                level_type: SimUniLevelType = level_type_from_id(level_type_id)
                if level_type is None:
                    continue
                level_type_list.append(level_type)

        text: str = ''
        for level_type in level_type_list:
            text += gt(level_type.type_name, 'ui') + '\n'

        self.level_type_text.value = text
        self.level_type_text.update()

    def _on_level_type_text_update(self, e):
        """
        楼层优先级的文本框输出改变
        :param e:
        :return:
        """
        type_name_list = self.get_str_list(self.level_type_text)
        level_type_list: List[SimUniLevelType] = []
        for type_name in type_name_list:
            level_type = level_type_from_name(type_name)
            if level_type is None:
                log.error('文本输入非法 %s 本次改动不保存', type_name)
                return  # 有一个错误就不继续了
            level_type_list.append(level_type)

        level_type_id_list = [level_type.type_id for level_type in level_type_list]
        self.chosen_config.level_type_priority = level_type_id_list

    def _on_curio_edit_clicked(self, e):
        """
        编辑奇物优先级
        :param e:
        :return:
        """
        self.curio_card.set_chosen_list(self.chosen_config.curio_priority)
        self._update_priority_status(self.curio_card, self.curio_text)

    def _on_curio_text_update(self, e):
        """
        奇物优先级的文本框输出改变
        :param e:
        :return:
        """
        curio_name_list = self.get_str_list(self.curio_text)
        curio_list: List[SimUniCurioEnum] = []
        for curio_name in curio_name_list:
            curio = curio_enum_from_name(curio_name)
            if curio is None:
                log.error('文本输入非法 %s 本次改动不保存', curio_name)
                return  # 有一个错误就不继续了
            curio_list.append(curio)

        curio_id_list = [curio.name for curio in curio_list]
        self.chosen_config.curio_priority = curio_id_list

    def _on_curio_priority_changed(self, curio_id_list: List[str]):
        """
        奇物优先级改变
        """
        self.chosen_config.curio_priority = curio_id_list
        self._update_curio_text()

    def _update_curio_text(self):
        """
        更新奇物优先级的文本
        :return:
        """
        curio_list: List[SimUniCurioEnum] = []
        if self.chosen_config is not None:
            for curio_id in self.chosen_config.curio_priority:
                curio_list.append(SimUniCurioEnum[curio_id])

        text: str = ''
        for curio in curio_list:
            text += gt(curio.value.name, 'ocr') + '\n'

        self.curio_text.value = text
        self.curio_text.update()

    def _on_max_consumable_cnt_changed(self, e):
        """
        单次使用消耗品个数
        :param e:
        :return:
        """
        self.chosen_config.max_consumable_cnt = int(self.max_consumable_cnt.value)

    @staticmethod
    def get_str_list(text_input: ft.TextField) -> List[str]:
        """
        从输入框分隔换行符得到目标
        :param text_input:
        :return:
        """
        arr = text_input.value.split('\n')
        if arr[len(arr) - 1] == '':
            arr.pop()
        return arr

    def _on_skip_herta_changed(self, e):
        """
        跳过黑塔更改
        :param e:
        :return:
        """
        self.chosen_config.skip_herta = self.skip_herta_checkbox.value

    def _on_technique_fight_changed(self, e):
        """
        秘技开怪更改
        :param e:
        :return:
        """
        self.chosen_config.technique_fight = self.technique_fight_checkbox.value

    def _on_technique_only_changed(self, e):
        """
        仅秘技开怪更改
        :param e:
        :return:
        """
        self.chosen_config.technique_only = self.technique_only_checkbox.value

    def _on_multiple_consumable_changed(self, e):
        """
        连续使用消耗品
        :param e:
        :return:
        """
        self.chosen_config.multiple_consumable = self.multiple_consumable_checkbox.value


_sim_uni_challenge_config_view: Optional[SimUniChallengeConfigView] = None


def get(page: ft.Page, ctx: Context) -> SimUniChallengeConfigView:
    global _sim_uni_challenge_config_view
    if _sim_uni_challenge_config_view is None:
        _sim_uni_challenge_config_view = SimUniChallengeConfigView(page, ctx)

    return _sim_uni_challenge_config_view

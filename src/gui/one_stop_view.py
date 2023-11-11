import flet as ft

from basic.i18_utils import gt
from gui import gui_const
from sr.context import Context

info_text_width = 200
info_text_spacing = 5
info_card_width = info_text_width * 2 + info_text_spacing
label_color = ft.colors.GREY_600
value_font_size = 20
value_font_weight = ft.FontWeight.W_500


class Label2NormalValueRow:

    def __init__(self, label: str, value: str, suffix_label: str = '',
                 width: int = 200, spacing: int = 5):
        self.label = ft.Text(value=label, color=label_color)
        self.value = ft.Text(value=value, size=value_font_size, weight=value_font_weight)
        self.suffix_label = ft.Text(value=suffix_label, color=label_color)
        self.component = ft.Row(controls=[self.label, self.value, self.suffix_label], spacing=spacing, width=width)


class Label2TimeValueRow:

    def __init__(self, label: str, hour: int, minute: int,
                 width: int = 200, spacing: int = 5):
        self.label = ft.Text(value=label, color=label_color)
        self.hour_value = ft.Text(value='%02d' % hour, size=value_font_size, weight=value_font_weight)
        self.hour_label = ft.Text(value='小时', color=label_color)
        self.minute_value = ft.Text(value='%02d' % minute, size=value_font_size, weight=value_font_weight)
        self.minute_label = ft.Text(value='分钟', color=label_color)
        self.component = ft.Row(controls=[
            self.label,
            ft.Row(controls=[self.hour_value, self.hour_label, self.minute_value, self.minute_label], spacing=0)
        ], spacing=spacing, width=width)


def card_title_text(title: str) -> ft.Text:
    return ft.Text(title, size=20, weight=ft.FontWeight.W_600, color=ft.colors.BLUE_300)


def card_container(content, title=None, width: int = 500) -> ft.Container:
    if title is not None:
        title_container = ft.Container(content=title, width=width, border=ft.border.only(bottom=ft.border.BorderSide(1, gui_const.DIVIDER_COLOR)))
        content_container = ft.Container(content=content, width=width, margin=ft.margin.only(top=5))
        final_content = ft.Column(controls=[title_container, content_container], spacing=0)
    else:
        final_content = content
    return ft.Container(content=final_content, border=ft.border.all(1, gui_const.DIVIDER_COLOR), padding=5, bgcolor='white',
                        shadow=ft.BoxShadow(
                            spread_radius=1,
                            blur_radius=15,
                            color=ft.colors.GREY_300,
                            offset=ft.Offset(0, 0),
                            blur_style=ft.ShadowBlurStyle.OUTER,
                        )
                        )


def app_list_item(title: str, app_id: str, last_run_time: str) -> ft.Row:
    text_col = ft.Column(controls=[
        ft.Container(content=ft.Text(title, weight=value_font_weight, size=value_font_size)),
        ft.Container(content=ft.Text(last_run_time, color=label_color, size=12))
    ], spacing=0, alignment=ft.MainAxisAlignment.CENTER)
    icon_col = ft.Row(controls=[
        ft.IconButton(icon=ft.icons.ARROW_UPWARD_OUTLINED, data=app_id, icon_size=20),
        ft.IconButton(icon=ft.icons.ARROW_DOWNWARD_OUTLINED, data=app_id, icon_size=20),
        ft.IconButton(icon=ft.icons.SETTINGS_OUTLINED, data=app_id, icon_size=20)
    ], spacing=5, expand=True, alignment=ft.MainAxisAlignment.END)  # 注意外部需要宽度
    return ft.Row(controls=[text_col, icon_col], height=50,
                  vertical_alignment=ft.CrossAxisAlignment.CENTER)


class AppList:

    def __init__(self):
        pass


class OneStopView:

    def __init__(self, page: ft.Page, ctx: Context):
        self.page = page
        self.ctx = ctx
        self.update_time = Label2NormalValueRow('数据更新时间', '2023-11-09 00:00:00', width=info_text_width*2)
        self.power = Label2NormalValueRow('开拓力', '200/240')

        self.power_recover = Label2TimeValueRow('剩余恢复时间', 12, 24)
        power_row = ft.Row(controls=[
            self.power.component,
            self.power_recover.component
        ])

        self.assignment_1_label = Label2TimeValueRow('委托1', 1, 24)
        self.assignment_2_label = Label2TimeValueRow('委托2', 2, 24)
        self.assignment_3_label = Label2TimeValueRow('委托3', 3, 24)
        self.assignment_4_label = Label2TimeValueRow('委托4', 4, 24)
        assignment_row_1 = ft.Row(controls=[self.assignment_1_label.component, self.assignment_2_label.component])
        assignment_row_2 = ft.Row(controls=[self.assignment_3_label.component, self.assignment_4_label.component])

        self.training = Label2NormalValueRow('实训', '500', '/500')
        self.echo = Label2NormalValueRow('历战回响', '3', '/3')
        training_row = ft.Row(controls=[self.training.component, self.echo.component])

        self.sim_rank = Label2NormalValueRow('模拟宇宙', '14000', '/14000')
        self.sim_times = Label2NormalValueRow('通关次数', '34')
        sim_row = ft.Row(controls=[self.sim_rank.component, self.sim_times.component])

        self.hall = Label2NormalValueRow('忘却之庭', '30', '/30')
        hall_row = ft.Row(controls=[self.hall.component])

        character_info_title = ft.Row(controls=[card_title_text('游戏角色状态(占坑 假的)')])
        character_info_content = ft.Column(controls=[
                self.update_time.component,
                power_row,
                assignment_row_1,
                assignment_row_2,
                training_row,
                sim_row,
                hall_row
            ], expand=True)
        character_info_card = card_container(character_info_content, title=character_info_title, width=info_card_width)

        self.running_ring = ft.ProgressRing(width=20, height=20, color=ft.colors.BLUE_300)
        status_title_row = ft.Row(controls=[
                card_title_text('脚本运行状态'),
                self.running_ring
            ], spacing=5)

        self.running_status = Label2NormalValueRow('运行中', '锄大地')
        self.next_job = Label2NormalValueRow('下一个', '无')
        status_content_row = ft.Row(controls=[self.running_status.component, self.next_job.component])

        status_card = card_container(status_content_row, title=status_title_row, width=info_card_width)

        status_part = ft.Container(content=ft.Column(controls=[status_card, character_info_card], spacing=10), padding=10)

        app_list = ft.ListView(controls=[
            ft.Container(app_list_item('锄大地', 'world_patrol', '2023-11-11 01:00:00'),
                         border=ft.border.only(bottom=ft.border.BorderSide(1, gui_const.DIVIDER_COLOR))),
            ft.Container(app_list_item('委托', 'assignments', '2023-11-11 01:00:00'),
                         border=ft.border.only(bottom=ft.border.BorderSide(1, gui_const.DIVIDER_COLOR))),
        ])

        app_list_card = card_container(app_list, title=card_title_text('任务列表'), width=300)
        app_list_part = ft.Container(content=app_list_card, padding=10)

        self.component = ft.Row(controls=[status_part, app_list_part], spacing=0)


osv: OneStopView = None


def get(page: ft.Page, ctx: Context):
    global osv
    if osv is None:
        osv = OneStopView(page, ctx)
    return osv

import threading
from typing import List

import flet as ft

from basic import win_utils
from basic.i18_utils import gt
from basic.log_utils import log
from gui import snack_bar, components, scheduler
from gui.settings import gui_config
from gui.settings.gui_config import ThemeColors
from sr.app import app_const, Application, one_stop_service, AppRunRecord
from sr.app.one_stop_service import OneStopService
from sr.context import Context

info_text_width = 200
info_text_spacing = 5
info_card_width = info_text_width * 2 + info_text_spacing
label_color = ft.colors.GREY_600
value_font_size = 20
value_font_weight = ft.FontWeight.W_500


class Label2NormalValueRow(ft.Row):

    def __init__(self, label: str, value: str, suffix_label: str = '',
                 width: int = 200, spacing: int = 5):
        self.label = ft.Text(value=label, color=label_color)
        self.value = ft.Text(value=value, size=value_font_size, weight=value_font_weight)
        self.suffix_label = ft.Text(value=suffix_label, color=label_color)
        super().__init__(controls=[self.label, self.value, self.suffix_label], spacing=spacing, width=width)

    def update_label(self, new_label: str):
        self.label.value = new_label
        self.update()

    def update_value(self, new_value: str):
        self.value.value = new_value
        self.update()


class Label2TimeValueRow(ft.Row):

    def __init__(self, label: str, hour: int, minute: int,
                 width: int = 200, spacing: int = 5):
        self.label = ft.Text(value=label, color=label_color)
        self.hour_value = ft.Text(value='%02d' % hour, size=value_font_size, weight=value_font_weight)
        self.hour_label = ft.Text(value='小时', color=label_color)
        self.minute_value = ft.Text(value='%02d' % minute, size=value_font_size, weight=value_font_weight)
        self.minute_label = ft.Text(value='分钟', color=label_color)
        super().__init__(controls=[
            self.label,
            ft.Row(controls=[self.hour_value, self.hour_label, self.minute_value, self.minute_label], spacing=0)
        ], spacing=spacing, width=width)


class AppListItem(ft.Row):

    def __init__(self, title: str, app_id: str,
                 on_click_run, on_click_up, on_click_down, on_click_settings):
        self.app_id: str = app_id
        theme: ThemeColors = gui_config.theme()
        self.run_status_text = ft.Text(gt('上次', 'ui'), color=label_color, size=12)
        self.run_status_running_icon = ft.Icon(name=ft.icons.ACCESS_TIME_FILLED, size=12, visible=False)
        self.run_status_success_icon = ft.Icon(name=ft.icons.CHECK_CIRCLE, size=12, color=theme['success_icon_color'], visible=False)
        self.run_status_fail_icon = ft.Icon(name=ft.icons.REMOVE_CIRCLE, size=12, color=theme['fail_icon_color'], visible=False)
        status_row = ft.Row(controls=[self.run_status_running_icon, self.run_status_success_icon, self.run_status_fail_icon, self.run_status_text], spacing=1,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER)
        text_col = ft.Column(controls=[
            ft.Container(content=ft.Text(title, weight=value_font_weight, size=18)),
            ft.Container(content=status_row)
        ], spacing=0, alignment=ft.MainAxisAlignment.CENTER)
        icon_col = ft.Row(controls=[
            ft.IconButton(icon=ft.icons.PLAY_ARROW_OUTLINED, data=app_id, icon_size=15, on_click=on_click_run),
            ft.IconButton(icon=ft.icons.ARROW_UPWARD_OUTLINED, data=app_id, icon_size=15, on_click=on_click_up),
            ft.IconButton(icon=ft.icons.ARROW_DOWNWARD_OUTLINED, data=app_id, icon_size=15, on_click=on_click_down),
            ft.IconButton(icon=ft.icons.SETTINGS_OUTLINED, data=app_id, icon_size=15, on_click=on_click_settings)
        ], spacing=0, expand=True, alignment=ft.MainAxisAlignment.END)  # 注意外部需要宽度固定
        super().__init__(controls=[text_col, icon_col], height=50,
                         vertical_alignment=ft.CrossAxisAlignment.CENTER)

    def update_status(self, app_record: AppRunRecord):
        status = app_record.run_status_under_now
        self.run_status_running_icon.visible = status == AppRunRecord.STATUS_RUNNING
        self.run_status_success_icon.visible = status == AppRunRecord.STATUS_SUCCESS
        self.run_status_fail_icon.visible = status == AppRunRecord.STATUS_FAIL
        self.run_status_text.value = gt('上次', 'ui') + ' ' + app_record.run_time
        self.update()


class AppList(ft.ListView):

    def __init__(self, run_app_callback):
        super().__init__()
        self.item_map: dict[str, AppListItem] = {}
        theme: ThemeColors = gui_config.theme()

        self.app_id_list: List[str] = one_stop_service.get_config().order_app_id_list
        for app_id in self.app_id_list:
            app = app_const.get_app_desc_by_id(app_id)
            item = AppListItem(app['cn'], app['id'],
                               on_click_run=self._on_item_click_run,
                               on_click_up=self._on_item_click_up,
                               on_click_down=self._on_item_click_down,
                               on_click_settings=self._on_item_click_settings
                               )
            self.item_map[app['id']] = item
            self.controls.append(ft.Container(
                content=item,
                border=ft.border.only(bottom=ft.border.BorderSide(1, theme['divider_color']))
            ))

        self.run_app_callback = run_app_callback

    def _on_item_click_run(self, e):
        self.run_app_callback(e.control.data)

    def _on_item_click_up(self, e):
        app_id: str = e.control.data
        target_idx: int = -1
        for i in range(len(self.controls)):
            item: AppListItem = self.controls[i].content
            if item.app_id == app_id:
                target_idx = i
                break

        if target_idx <= 0:
            return
        temp = self.controls[target_idx - 1]
        self.controls[target_idx - 1] = self.controls[target_idx]
        self.controls[target_idx] = temp

        temp = self.app_id_list[target_idx - 1]
        self.app_id_list[target_idx - 1] = self.app_id_list[target_idx]
        self.app_id_list[target_idx] = temp
        one_stop_service.get_config().order_app_id_list = self.app_id_list

    def _on_item_click_down(self, e):
        app_id: str = e.control.data
        target_idx: int = len(self.controls)
        for i in range(len(self.controls)):
            item: AppListItem = self.controls[i].content
            if item.app_id == app_id:
                target_idx = i
                break

        if target_idx >= len(self.controls) - 1:
            return
        temp = self.controls[target_idx + 1]
        self.controls[target_idx + 1] = self.controls[target_idx]
        self.controls[target_idx] = temp

        temp = self.app_id_list[target_idx + 1]
        self.app_id_list[target_idx + 1] = self.app_id_list[target_idx]
        self.app_id_list[target_idx] = temp
        one_stop_service.get_config().order_app_id_list = self.app_id_list

    def _on_item_click_settings(self, e):
        pass

    def update_all_app_status(self):
        for app_id in self.app_id_list:
            app_record = one_stop_service.get_app_run_record_by_id(app_id)
            if app_record is not None:
                self.item_map[app_id].update_status(app_record)


class OneStopView(ft.Row):

    def __init__(self, page: ft.Page, ctx: Context):
        self.page: ft.Page = page
        self.ctx: Context = ctx
        theme: ThemeColors = gui_config.theme()

        self.update_time = Label2NormalValueRow('数据更新时间', '2023-11-09 00:00:00', width=info_text_width*2)
        self.power = Label2NormalValueRow('开拓力', '200/240')

        self.power_recover = Label2TimeValueRow('剩余恢复时间', 12, 24)
        power_row = ft.Row(controls=[
            self.power,
            self.power_recover
        ])

        self.assignment_1_label = Label2TimeValueRow('委托1', 1, 24)
        self.assignment_2_label = Label2TimeValueRow('委托2', 2, 24)
        self.assignment_3_label = Label2TimeValueRow('委托3', 3, 24)
        self.assignment_4_label = Label2TimeValueRow('委托4', 4, 24)
        assignment_row_1 = ft.Row(controls=[self.assignment_1_label, self.assignment_2_label])
        assignment_row_2 = ft.Row(controls=[self.assignment_3_label, self.assignment_4_label])

        self.training = Label2NormalValueRow('实训', '500', '/500')
        self.echo = Label2NormalValueRow('历战回响', '3', '/3')
        training_row = ft.Row(controls=[self.training, self.echo])

        self.sim_rank = Label2NormalValueRow('模拟宇宙', '14000', '/14000')
        self.sim_times = Label2NormalValueRow('通关次数', '34')
        sim_row = ft.Row(controls=[self.sim_rank, self.sim_times])

        self.hall = Label2NormalValueRow('忘却之庭', '30', '/30')
        hall_row = ft.Row(controls=[self.hall])

        character_info_title = ft.Row(controls=[components.CardTitleText('游戏角色状态(占坑 假的)')])
        character_info_content = ft.ListView(controls=[
                self.update_time,
                power_row,
                assignment_row_1,
                assignment_row_2,
                training_row,
                sim_row,
                hall_row
            ], auto_scroll=True)
        character_info_card = components.Card(character_info_content, title=character_info_title, width=info_card_width, height=250)

        self.running_ring = ft.ProgressRing(width=20, height=20, color=ft.colors.BLUE_300, visible=False)
        status_title_row = ft.Row(controls=[
                components.CardTitleText('脚本运行状态'),
                self.running_ring
            ], spacing=5)

        self.running_status = Label2NormalValueRow('空闲', '')
        self.next_job = Label2NormalValueRow('下一个', '无')
        status_content_row = ft.Row(controls=[self.running_status, self.next_job])

        self.shutdown_check = ft.Checkbox(label=gt("结束后关机", model='ui'), value=False, on_change=self.on_shutdown_changed)
        shutdown_row = ft.Row(controls=[self.shutdown_check], alignment=ft.MainAxisAlignment.CENTER)

        self.start_btn = components.RectOutlinedButton(text=gt("F9 开始", model='ui'), on_click=self.on_click_start)
        self.pause_btn = components.RectOutlinedButton(text=gt("F9 暂停", model='ui'), on_click=self.on_click_pause, visible=False)
        self.resume_btn = components.RectOutlinedButton(text=gt("F9 继续", model='ui'), on_click=self.on_click_resume, visible=False)
        self.stop_btn = components.RectOutlinedButton(text=gt("F10 结束", model='ui'), on_click=self.on_click_stop, disabled=True)
        ctrl_btn_row = ft.Row(controls=[self.start_btn, self.pause_btn, self.resume_btn, self.stop_btn],
                              alignment=ft.MainAxisAlignment.CENTER)

        status_content = ft.Column(controls=[status_content_row, shutdown_row, ctrl_btn_row], auto_scroll=True)

        status_card = components.Card(status_content, title=status_title_row, width=info_card_width, height=150)

        left_part = ft.Container(ft.Column(controls=[character_info_card, status_card], spacing=10))

        self.app_list = AppList(run_app_callback=self.run_app)

        app_list_card = components.Card(self.app_list, title=components.CardTitleText('任务列表'), width=300)
        app_list_part = ft.Container(content=app_list_card)

        super().__init__(controls=[left_part, app_list_part], spacing=10)

        self.ctx.register_status_changed_handler(self,
                                                 self._after_start,
                                                 self._after_pause,
                                                 self._after_resume,
                                                 self._after_stop
                                                 )

        self.running_app: Application
        scheduler.every_second(self._update_app_list_status, tag='_update_app_list_status')

    def _check_ctx_stop(self) -> bool:
        """
        检查是否在停止状态
        :return: 是否在停止状态
        """
        if not self.ctx.is_stop:
            msg: str = '其它任务正在执行 请先完成或停止'
            snack_bar.show_message(msg, self.page)
            log.info(msg)
            return False
        return True

    def run_app(self, app_id: str):
        if not self._check_ctx_stop():
            return

        self.running_app: Application = one_stop_service.get_app_by_id(app_id, self.ctx)
        if self.running_app is None:
            log.error('非法的任务入参')
            self.running_app = None
            return

        t = threading.Thread(target=self.running_app.execute)
        t.start()

    def on_click_start(self, e):
        if not self._check_ctx_stop():
            return
        self.start_btn.disabled = True
        self.update()
        self.running_app = OneStopService(self.ctx, app_const.ROUTINE_APP_LIST)

        t = threading.Thread(target=self.running_app.execute)
        t.start()

    def on_click_pause(self, e):
        self.ctx.switch()

    def on_click_resume(self, e):
        self.ctx.switch()

    def on_click_stop(self, e):
        self.ctx.stop_running()

    def _update_status_component(self):
        """
        更新显示状态相关的组件
        :return:
        """
        self.start_btn.visible = self.ctx.is_stop
        self.start_btn.disabled = False
        self.pause_btn.visible = self.ctx.is_running
        self.resume_btn.visible = self.ctx.is_pause
        self.stop_btn.disabled = self.ctx.is_stop
        self.running_ring.visible = self.ctx.is_running
        self.running_status.update_label(self.ctx.status_text)
        self.update()

    def _after_start(self):
        self._update_status_component()
        scheduler.every_second(self._update_running_app_name, tag='_update_running_app_name')

    def _after_pause(self):
        self._update_status_component()

    def _after_resume(self):
        self._update_status_component()

    def _after_stop(self):
        self._update_status_component()
        scheduler.cancel_with_tag('_update_running_app_name')
        self.running_app = None
        self._update_running_app_name()
        if self.shutdown_check.value:
            log.info('执行完毕 准备关机')
            win_utils.shutdown_sys(60)

    def on_shutdown_changed(self, e):
        if not self.shutdown_check.value:
            log.info('已取消关机计划')
            win_utils.cancel_shutdown_sys()

    def _update_running_app_name(self):
        if self.running_app is None:
            self.running_status.update_value('')
            self.next_job.update_value(gt('无', 'ui'))
        else:
            self.running_status.update_value(self.running_app.current_execution_desc)
            self.next_job.update_value(self.running_app.next_execution_desc)

    def _update_app_list_status(self):
        self.app_list.update_all_app_status()


osv: OneStopView = None


def get(page: ft.Page, ctx: Context):
    global osv
    if osv is None:
        osv = OneStopView(page, ctx)
    return osv

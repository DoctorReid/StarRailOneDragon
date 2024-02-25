import subprocess
import threading
import time
from typing import Optional, List

import keyboard
import pyautogui

from basic import os_utils
from basic.i18_utils import gt
from basic.img.os import save_debug_image
from basic.log_utils import log
from sr.app.assignments.assignments_run_record import AssignmentsRunRecord
from sr.app.buy_xianzhou_parcel.buy_xianzhou_parcel_run_record import BuyXianZhouParcelRunRecord
from sr.app.daily_training.daily_training_run_record import DailyTrainingRunRecord
from sr.app.echo_of_war.echo_of_war_config import EchoOfWarConfig
from sr.app.echo_of_war.echo_of_war_run_record import EchoOfWarRunRecord
from sr.app.email.email_run_record import EmailRunRecord
from sr.app.nameless_honor.nameless_honor_run_record import NamelessHonorRunRecord
from sr.app.sim_uni.sim_uni_config import SimUniConfig
from sr.app.sim_uni.sim_uni_run_record import SimUniRunRecord
from sr.app.support_character.support_character_run_record import SupportCharacterRunRecord
from sr.app.trailblaze_power.trailblaze_power_config import TrailblazePowerConfig
from sr.app.trailblaze_power.trailblaze_power_run_record import TrailblazePowerRunRecord
from sr.app.treasures_lightward.treasures_lightward_config import TreasuresLightwardConfig
from sr.app.treasures_lightward.treasures_lightward_record import TreasuresLightwardRunRecord
from sr.app.world_patrol.world_patrol_config import WorldPatrolConfig
from sr.app.world_patrol.world_patrol_run_record import WorldPatrolRunRecord
from sr.config.game_config import GameConfig
from sr.const import game_config_const
from sr.const.character_const import Character, TECHNIQUE_BUFF, TECHNIQUE_BUFF_ATTACK
from sr.control import GameController
from sr.control.pc_controller import PcController
from sr.image import ImageMatcher
from sr.image.cn_ocr_matcher import CnOcrMatcher
from sr.image.cv2_matcher import CvImageMatcher
from sr.image.en_ocr_matcher import EnOcrMatcher
from sr.image.image_holder import ImageHolder
from sr.image.ocr_matcher import OcrMatcher
from sr.image.sceenshot import fill_uid_black
from sr.one_dragon_config import OneDragonConfig, OneDragonAccount
from sr.performance_recorder import PerformanceRecorder, get_recorder, log_all_performance
from sr.win import Window


class Context:

    def __init__(self):
        """
        用于存放运行时的上下文
        """
        self.platform: str = 'PC'
        self.ih: ImageHolder = ImageHolder()
        self.im: Optional[ImageMatcher] = None
        self.ocr: Optional[OcrMatcher] = None
        self.controller: Optional[GameController] = None
        self.running: int = 0  # 0-停止 1-运行 2-暂停
        self.press_event: dict = {}
        self.start_callback: dict = {}
        self.pause_callback: dict = {}
        self.resume_callback: dict = {}
        self.stop_callback: dict = {}

        self.recorder: PerformanceRecorder = get_recorder()
        self.open_game_by_script: bool = False  # 脚本启动的游戏
        self.first_transport: bool = True  # 第一次传送

        self.current_character_list: List[Character] = []
        self.technique_used: bool = False  # 新一轮战斗前是否已经使用秘技了

        self.one_dragon_config: OneDragonConfig = OneDragonConfig()
        self.game_config: Optional[GameConfig] = None

        self.world_patrol_config: Optional[WorldPatrolConfig] = None
        self.world_patrol_run_record: Optional[WorldPatrolRunRecord] = None

        self.tp_config: Optional[TrailblazePowerConfig] = None
        self.tp_run_record: Optional[TrailblazePowerRunRecord] = None

        self.echo_config: Optional[EchoOfWarConfig] = None
        self.echo_run_record: Optional[EchoOfWarRunRecord] = None

        self.tl_config: Optional[TreasuresLightwardConfig] = None
        self.tl_run_record: Optional[TreasuresLightwardRunRecord] = None

        self.sim_uni_config: Optional[SimUniConfig] = None
        self.sim_uni_run_record: Optional[SimUniRunRecord] = None

        self.assignments_run_record: Optional[AssignmentsRunRecord] = None
        self.buy_xz_parcel_run_record: Optional[BuyXianZhouParcelRunRecord] = None
        self.daily_training_run_record: Optional[DailyTrainingRunRecord] = None
        self.email_run_record: Optional[EmailRunRecord] = None
        self.nameless_honor_run_record: Optional[NamelessHonorRunRecord] = None
        self.support_character_run_record: Optional[SupportCharacterRunRecord] = None

        self.init_if_no_account()
        self.init_config_by_account()
        self.init_keyboard_callback()

    def init_if_no_account(self):
        """
        无账号时做的初始化
        :return:
        """
        if len(self.one_dragon_config.account_list) > 0:
            return
        account: OneDragonAccount = self.one_dragon_config.create_new_account(True)
        account_idx = account.idx

        self.game_config = GameConfig()
        self.game_config.move_to_account_idx(account_idx)

        # 锄大地移动了目录 需要自己重新设置
        # self.world_patrol_config = WorldPatrolConfig()
        # self.world_patrol_config.move_to_account_idx(account_idx)
        self.world_patrol_run_record = WorldPatrolRunRecord()
        self.world_patrol_run_record.move_to_account_idx(account_idx)

        self.tp_config = TrailblazePowerConfig()
        self.tp_config.move_to_account_idx(account_idx)
        self.tp_run_record = TrailblazePowerRunRecord(self.tp_config)
        self.tp_run_record.move_to_account_idx(account_idx)

        self.echo_config = EchoOfWarConfig()
        self.echo_config.move_to_account_idx(account_idx)
        self.echo_run_record = EchoOfWarRunRecord()
        self.echo_run_record.move_to_account_idx(account_idx)

        self.tl_config = TreasuresLightwardConfig()
        self.tl_config.move_to_account_idx(account_idx)
        self.tl_run_record = TreasuresLightwardRunRecord()
        self.tl_run_record.move_to_account_idx(account_idx)

        self.sim_uni_config = SimUniConfig()
        self.sim_uni_config.move_to_account_idx(account_idx)
        self.sim_uni_run_record = SimUniRunRecord(self.sim_uni_config)
        self.sim_uni_run_record.move_to_account_idx(account_idx)

        self.assignments_run_record = AssignmentsRunRecord()
        self.assignments_run_record.move_to_account_idx(account_idx)

        self.buy_xz_parcel_run_record = BuyXianZhouParcelRunRecord()
        self.buy_xz_parcel_run_record.move_to_account_idx(account_idx)

        self.daily_training_run_record = DailyTrainingRunRecord()
        self.daily_training_run_record.move_to_account_idx(account_idx)

        self.email_run_record = EmailRunRecord()
        self.email_run_record.move_to_account_idx(account_idx)

        self.nameless_honor_run_record = NamelessHonorRunRecord()
        self.nameless_honor_run_record.move_to_account_idx(account_idx)

        self.support_character_run_record = SupportCharacterRunRecord()
        self.support_character_run_record.move_to_account_idx(account_idx)

    def init_config_by_account(self):
        """
        加载账号对应的配置
        :return:
        """
        account_idx = self.one_dragon_config.current_active_account.idx
        self.game_config = GameConfig(account_idx)

        self.world_patrol_config = WorldPatrolConfig(account_idx)
        self.world_patrol_run_record = WorldPatrolRunRecord(account_idx)

        self.tp_config = TrailblazePowerConfig(account_idx)
        self.tp_run_record = TrailblazePowerRunRecord(self.tp_config, account_idx)

        self.echo_config = EchoOfWarConfig(account_idx)
        self.echo_run_record = EchoOfWarRunRecord(account_idx)

        self.tl_config = TreasuresLightwardConfig(account_idx)
        self.tl_run_record = TreasuresLightwardRunRecord(account_idx)

        self.sim_uni_config = SimUniConfig()
        self.sim_uni_run_record = SimUniRunRecord(self.sim_uni_config)

        self.assignments_run_record = AssignmentsRunRecord(account_idx)
        self.buy_xz_parcel_run_record = BuyXianZhouParcelRunRecord(account_idx)
        self.daily_training_run_record = DailyTrainingRunRecord(account_idx)
        self.email_run_record = EmailRunRecord(account_idx)
        self.nameless_honor_run_record = NamelessHonorRunRecord(account_idx)
        self.support_character_run_record = SupportCharacterRunRecord(account_idx)

    def init_keyboard_callback(self):
        """
        注册按键监听
        :return:
        """
        keyboard.on_press(self.on_key_press)
        self.register_key_press('f9', self.switch)
        self.register_key_press('f10', self.stop_running)
        self.register_key_press('f11', self.screenshot)
        if self.platform == 'PC':
            self.register_key_press('f12', self.mouse_position)

    def register_key_press(self, key, callback):
        if key not in self.press_event:
            self.press_event[key] = []
        self.press_event[key].append(callback)

    def on_key_press(self, event):
        k = event.name
        if k in self.press_event:
            log.debug('触发按键 %s', k)
            for callback in self.press_event[k]:
                callback()

    def start_running(self) -> bool:
        if self.running != 0:
            log.error('请先结束其他运行中的功能 再启动')
            return False

        if not self.init_all(renew=True):
            self.stop_running()
            return False

        self.running = 1
        self.controller.init()
        self._after_start()
        return True

    @property
    def is_stop(self) -> bool:
        return self.running == 0

    @property
    def is_running(self) -> bool:
        return self.running == 1

    @property
    def is_pause(self) -> bool:
        return self.running == 2

    @property
    def status_text(self) -> str:
        if self.running == 0:
            return gt('空闲', 'ui')
        elif self.running == 1:
            return gt('运行中', 'ui')
        elif self.running == 2:
            return gt('暂停中', 'ui')
        else:
            return 'unknow'

    def _after_start(self):
        for obj_id, callback in self.start_callback.items():
            t = threading.Thread(target=callback)
            t.start()

    def stop_running(self):
        if self.running == 0:
            return
        log.info('停止运行')  # 这里不能先判断 self.running == 0 就退出 因为有可能启动初始化就失败 这时候需要触发 after_stop 回调各方
        if self.running == 1:  # 先触发暂停 让执行中的指令停止
            self.switch()
        self.running = 0
        self._after_stop()

    def _after_stop(self):
        for obj_id, callback in self.stop_callback.items():
            t = threading.Thread(target=callback)
            t.start()

        if os_utils.is_debug():
            log_all_performance()

    def switch(self):
        if self.running == 1:
            log.info('暂停运行')
            self.running = 2
            self._after_pause()
        elif self.running == 2:
            log.info('恢复运行')
            self.running = 1
            self._after_resume()

    def _after_pause(self):
        callback_arr = self.pause_callback.copy()
        for obj_id, callback in callback_arr.items():
            t = threading.Thread(target=callback)
            t.start()

    def _after_resume(self):
        callback_arr = self.resume_callback.copy()
        for obj_id, callback in callback_arr.items():
            t = threading.Thread(target=callback)
            t.start()

    def register_status_changed_handler(self, obj,
                                        after_start_callback=None,
                                        after_pause_callback=None,
                                        after_resume_callback=None,
                                        after_stop_callback=None):
        if after_start_callback is not None:
            self.start_callback[id(obj)] = after_start_callback
        if after_pause_callback is not None:
            self.pause_callback[id(obj)] = after_pause_callback
        if after_resume_callback is not None:
            self.resume_callback[id(obj)] = after_resume_callback
        if after_stop_callback is not None:
            self.stop_callback[id(obj)] = after_stop_callback

    def register_pause(self, obj,
                       pause_callback,
                       resume_callback):
        self.pause_callback[id(obj)] = pause_callback
        self.resume_callback[id(obj)] = resume_callback

    def register_stop(self, obj, stop_callback):
        self.stop_callback[id(obj)] = stop_callback

    def unregister(self, obj):
        if id(obj) in self.start_callback:
            del self.start_callback[id(obj)]
        if id(obj) in self.pause_callback:
            del self.pause_callback[id(obj)]
        if id(obj) in self.resume_callback:
            del self.resume_callback[id(obj)]
        if id(obj) in self.stop_callback:
            del self.stop_callback[id(obj)]

    def init_controller(self, renew: bool = False) -> bool:
        self.open_game_by_script = False
        if renew:
            self.controller = None
        try:
            if self.controller is None:
                if self.platform == 'PC':
                    win = get_game_win()
                    win.active()
                    self.controller = PcController(win=win, ocr=self.ocr)

        except pyautogui.PyAutoGUIException:
            log.info('未开打游戏')
            if not self.try_open_game():
                return False

            self.first_transport = True  # 重新打开游戏的话 重置一下

            for i in range(30):
                if self.running == 0:
                    break
                time.sleep(1)
                try:
                    self.controller = PcController(win=get_game_win(), ocr=self.ocr)
                    self.running = 0
                    break
                except pyautogui.PyAutoGUIException:
                    log.info('未检测到游戏窗口 等待中')

            if self.controller is None:
                log.error('未能检测到游戏窗口')
                return False
            self.open_game_by_script = True
        log.info('加载游戏控制器完毕')
        return True

    def init_image_matcher(self, renew: bool = False) -> bool:
        if renew:
            self.im = None
        if self.im is None:
            self.im = CvImageMatcher(self.ih)
        log.info('加载图片匹配器完毕')
        return True

    def init_ocr_matcher(self, renew: bool = False) -> bool:
        if renew:
            self.ocr = None
        if self.ocr is None:
            self.ocr = get_ocr_matcher(self.game_config.lang)
        log.info('加载OCR识别器完毕')
        return True

    def init_all(self, renew: bool = False) -> bool:
        log.info('加载工具中')
        result: bool = True
        result = result and self.init_image_matcher(renew)
        result = result and self.init_ocr_matcher(renew)
        result = result and self.init_controller(renew)
        if result:
            log.info('加载工具完毕')
        return result

    def mouse_position(self):
        self.init_controller(False)
        rect = self.controller.win.get_win_rect()
        pos = pyautogui.position()
        log.info('当前鼠标坐标 %s', (pos.x - rect.x, pos.y - rect.y))

    def screenshot(self):
        """
        仅供快捷键使用 命令途中获取截图请使用 controller.screenshot()
        :return:
        """
        self.init_controller(False)
        save_debug_image(fill_uid_black(self.controller.screenshot()))

    @property
    def is_buff_technique(self) -> bool:
        """
        当前角色使用的秘技是否buff类型
        :return:
        """
        if self.current_character_list is None or len(self.current_character_list) == 0:
            return False
        if self.current_character_list[0] is None:  # TODO 缺少当前角色的判断
            return False
        return self.current_character_list[0].technique_type in (TECHNIQUE_BUFF, TECHNIQUE_BUFF_ATTACK)

    @property
    def is_pc(self) -> bool:
        return self.platform == 'PC'

    def try_open_game(self) -> bool:
        """
        尝试打开游戏 如果有配置游戏路径的话
        :return:
        """
        if self.game_config.game_path == '':
            log.info('未配置游戏路径 无法自动启动')
            return False
        global_context.running = 1
        log.info('尝试自动启动游戏 路径为 %s', self.game_config.game_path)
        subprocess.Popen(self.game_config.game_path)
        return True


def get_game_win() -> Window:
    return Window(gt('崩坏：星穹铁道', model='ui'))


_ocr_matcher = {}


def get_ocr_matcher(lang: str) -> OcrMatcher:
    matcher: OcrMatcher = None
    if lang not in _ocr_matcher:
        if lang == game_config_const.LANG_CN:
            matcher = CnOcrMatcher()
        elif lang == game_config_const.LANG_EN:
            matcher = EnOcrMatcher()
        _ocr_matcher[lang] = matcher
    else:
        matcher = _ocr_matcher[lang]
    return matcher


global_context: Context = Context()


def get_context() -> Context:
    global global_context
    return global_context


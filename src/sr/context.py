import subprocess
import time
from enum import Enum
from typing import Optional, List

import keyboard
import pyautogui

from basic import os_utils
from basic.i18_utils import gt
from basic.img.os import save_debug_image
from basic.log_utils import log
from sr.app.assignments.assignments_run_record import AssignmentsRunRecord
from sr.app.buy_xianzhou_parcel.buy_xianzhou_parcel_run_record import BuyXianZhouParcelRunRecord
from sr.app.claim_email.email_run_record import EmailRunRecord
from sr.app.daily_training.daily_training_run_record import DailyTrainingRunRecord
from sr.app.echo_of_war.echo_of_war_config import EchoOfWarConfig
from sr.app.echo_of_war.echo_of_war_run_record import EchoOfWarRunRecord
from sr.app.mys.mys_run_record import MysRunRecord
from sr.app.nameless_honor.nameless_honor_run_record import NamelessHonorRunRecord
from sr.app.one_stop_service.one_stop_service_config import OneStopServiceConfig
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
from sr.const.character_const import Character, TECHNIQUE_BUFF, TECHNIQUE_BUFF_ATTACK, TECHNIQUE_ATTACK
from sr.const.map_const import Planet, Region
from sr.control import GameController
from sr.control.pc_controller import PcController
from sr.event_bus import EventBus
from sr.image import ImageMatcher
from sr.image.cn_ocr_matcher import CnOcrMatcher
from sr.image.cv2_matcher import CvImageMatcher
from sr.image.en_ocr_matcher import EnOcrMatcher
from sr.image.image_holder import ImageHolder
from sr.image.ocr_matcher import OcrMatcher
from sr.image.sceenshot import fill_uid_black
from sr.image.yolo_screen_detector import get_yolo_model_parent_dir
from sr.mystools.one_dragon_mys_config import MysConfig
from sr.one_dragon_config import OneDragonConfig, OneDragonAccount
from sr.performance_recorder import PerformanceRecorder, get_recorder, log_all_performance
from sr.sim_uni.sim_uni_challenge_config import SimUniChallengeAllConfig, SimUniChallengeConfig
from sr.win import Window
from sryolo.detector import StarRailYOLO


class PosInfo:

    def __init__(self, planet: Optional[Planet] = None, region: Optional[Region] = None):
        """
        当前位置信息 包含大地图
        """
        self.large_map_scale: int = 5  # 当前大地图缩放比例
        self.planet: Planet = planet
        self.region: Region = region

        self.cancel_mission_trace: bool = False
        """是否已经取消了任务追踪"""

        self.first_cal_pos_after_fight: bool = False


class TeamInfo:

    def __init__(self,
                 character_list: Optional[List[Character]] = None,
                 current_active: int = 0):
        """
        当前组队信息
        """
        self.character_list: List[Character] = character_list
        self.current_active: int = current_active  # 当前使用的是第几个角色

    @property
    def is_attack_technique(self) -> bool:
        """
        当前角色使用的秘技是否buff类型
        :return:
        """
        if self.character_list is None or len(self.character_list) == 0:
            return False
        if self.current_active < 0 or self.current_active >= len(self.character_list):
            return False
        if self.character_list[self.current_active] is None:
            return False
        return self.character_list[self.current_active].technique_type in [TECHNIQUE_ATTACK]

    @property
    def is_buff_technique(self) -> bool:
        """
        当前角色使用的秘技是否buff类型
        :return:
        """
        if self.character_list is None or len(self.character_list) == 0:
            return False
        if self.current_active < 0 or self.current_active >= len(self.character_list):
            return False
        if self.character_list[self.current_active] is None:
            return False
        return self.character_list[self.current_active].technique_type in [TECHNIQUE_BUFF, TECHNIQUE_BUFF_ATTACK]

    def update_character_list(self, new_character_list: List[Character]):
        self.character_list = new_character_list


class SimUniInfo:

    def __init__(self):
        """
        模拟宇宙信息
        """
        self.world_num: int = 0  # 当前第几世界


class DetectInfo:

    def __init__(self):
        """
        用于目标检测的一些信息
        """
        self.view_down: bool = False  # 当前视角是否已经下移 形成俯视角度


class ContextEventId(Enum):

    CONTEXT_START: str = '运行开始'
    CONTEXT_PAUSE: str = '运行暂停'
    CONTEXT_RESUME: str = '运行继续'
    CONTEXT_STOP: str = '运行结束'


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
        self._sim_uni_yolo: Optional[StarRailYOLO] = None
        self.running: int = 0  # 0-停止 1-运行 2-暂停
        self.press_event: dict = {}
        self.event_bus: EventBus = EventBus()

        self.recorder: PerformanceRecorder = get_recorder()

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
        self.sim_uni_challenge_all_config: Optional[SimUniChallengeAllConfig] = None
        self.sim_uni_run_record: Optional[SimUniRunRecord] = None

        self.mys_config: Optional[MysConfig] = None
        self.mys_run_record: Optional[MysRunRecord] = None

        self.assignments_run_record: Optional[AssignmentsRunRecord] = None
        self.buy_xz_parcel_run_record: Optional[BuyXianZhouParcelRunRecord] = None
        self.daily_training_run_record: Optional[DailyTrainingRunRecord] = None
        self.email_run_record: Optional[EmailRunRecord] = None
        self.nameless_honor_run_record: Optional[NamelessHonorRunRecord] = None
        self.support_character_run_record: Optional[SupportCharacterRunRecord] = None

        self.one_stop_service_config: Optional[OneStopServiceConfig] = None

        self.init_if_no_account()
        self.init_config_by_account()
        self.init_keyboard_callback()

        self.open_game_by_script: bool = False  # 脚本启动的游戏
        self.current_character_list: List[Character] = []
        self.technique_used: bool = False  # 新一轮战斗前是否已经使用秘技了
        self.no_technique_recover_consumables: bool = False  # 没有恢复秘技的物品了 为True的时候就不使用秘技了
        self.consumable_used: bool = False  # 是否已经使用过消耗品了

        self.pos_info: PosInfo = PosInfo()
        self.team_info: TeamInfo = TeamInfo()
        self.sim_uni_info: SimUniInfo = SimUniInfo()
        self.detect_info: DetectInfo = DetectInfo()

        self.record_coordinate: bool = False  # 需要记录坐标用于训练

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

        self.mys_config = MysConfig(account_idx)
        self.mys_run_record = MysRunRecord(account_idx)

        self.world_patrol_config = WorldPatrolConfig()
        self.world_patrol_config.move_to_account_idx(account_idx)
        self.world_patrol_run_record = WorldPatrolRunRecord()
        self.world_patrol_run_record.move_to_account_idx(account_idx)

        self.tp_config = TrailblazePowerConfig()
        self.tp_config.move_to_account_idx(account_idx)
        self.tp_run_record = TrailblazePowerRunRecord(self.tp_config, self.mys_config)
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

        self.assignments_run_record = AssignmentsRunRecord(self.mys_config)
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

        self.one_stop_service_config = OneStopServiceConfig()
        self.one_stop_service_config.move_to_account_idx(account_idx)

    def init_config_by_account(self):
        """
        加载账号对应的配置
        :return:
        """
        account_idx = self.one_dragon_config.current_active_account.idx
        self.game_config = GameConfig(account_idx)

        self.mys_config = MysConfig(account_idx)
        self.mys_run_record = MysRunRecord(account_idx)

        self.world_patrol_config = WorldPatrolConfig(account_idx)
        self.world_patrol_run_record = WorldPatrolRunRecord(account_idx)

        self.tp_config = TrailblazePowerConfig(account_idx)
        self.tp_run_record = TrailblazePowerRunRecord(self.tp_config, self.mys_config, account_idx)

        self.echo_config = EchoOfWarConfig(account_idx)
        self.echo_run_record = EchoOfWarRunRecord(account_idx)

        self.tl_config = TreasuresLightwardConfig(account_idx)
        self.tl_run_record = TreasuresLightwardRunRecord(account_idx)

        self.sim_uni_config = SimUniConfig(account_idx)
        self.sim_uni_challenge_all_config = SimUniChallengeAllConfig()
        self.sim_uni_run_record = SimUniRunRecord(self.sim_uni_config, account_idx)

        self.assignments_run_record = AssignmentsRunRecord(self.mys_config, account_idx)
        self.buy_xz_parcel_run_record = BuyXianZhouParcelRunRecord(account_idx)
        self.daily_training_run_record = DailyTrainingRunRecord(account_idx)
        self.email_run_record = EmailRunRecord(account_idx)
        self.nameless_honor_run_record = NamelessHonorRunRecord(account_idx)
        self.support_character_run_record = SupportCharacterRunRecord(account_idx)

        self.one_stop_service_config = OneStopServiceConfig(account_idx)

    def active_account(self, account_idx: int):
        """
        启用一个账号 其他账号将会设置为不启用
        :param account_idx:
        :return:
        """
        if account_idx == self.one_dragon_config.current_active_account.idx:
            log.info('当前账号已启用 无需切换')
            return

        self.one_dragon_config.active_account(account_idx)
        log.info('切换启用账号 %s', self.one_dragon_config.current_active_account.name)
        self.init_config_by_account()

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
        if self.controller is not None:
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
        self.event_bus.dispatch_event(ContextEventId.CONTEXT_START.value)

    def stop_running(self):
        if self.running == 0:  # 初始化失败了 还没开始运行就要结束 依然触发一次停止的回调 方便使用方知道
            self._after_stop()
            return
        log.info('停止运行')  # 这里不能先判断 self.running == 0 就退出 因为有可能启动初始化就失败 这时候需要触发 after_stop 回调各方
        if self.running == 1:  # 先触发暂停 让执行中的指令停止
            self.switch()
        self.running = 0
        self._after_stop()

    def _after_stop(self):
        self.event_bus.dispatch_event(ContextEventId.CONTEXT_STOP.value)
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
        self.event_bus.dispatch_event(ContextEventId.CONTEXT_PAUSE.value)

    def _after_resume(self):
        self.event_bus.dispatch_event(ContextEventId.CONTEXT_RESUME.value)

    def init_controller(self, renew: bool = False) -> bool:
        self.open_game_by_script = False
        if renew:
            self.controller = None
        try:
            if self.controller is None:
                if self.platform == 'PC':
                    win = get_game_win()
                    win.active()
                    self.controller = PcController(win=win, ocr=self.ocr, gc=self.game_config)

        except pyautogui.PyAutoGUIException:
            log.info('未开打游戏')
            if not self.try_open_game():
                return False

            for i in range(30):
                if self.running == 0:
                    break
                time.sleep(1)
                try:
                    self.controller = PcController(win=get_game_win(), ocr=self.ocr, gc=self.game_config)
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
        img = self.controller.screenshot()
        fill_uid_black(img)
        save_debug_image(img)

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

    def init_after_enter_game(self):
        """
        进入游戏后需要做的初始化
        :return:
        """
        self.pos_info.large_map_scale = 5
        self.no_technique_recover_consumables = False

    def init_before_app_start(self):
        """
        应用开始前的初始化
        :return:
        """
        self.pos_info.planet = None
        self.pos_info.region = None
        self.pos_info.first_cal_pos_after_fight = False

    @property
    def sim_uni_challenge_config(self) -> Optional[SimUniChallengeConfig]:
        if self.sim_uni_info.world_num == 0 or self.sim_uni_config is None:
            return None
        else:
            return self.sim_uni_config.get_challenge_config(self.sim_uni_info.world_num)

    @property
    def sim_uni_yolo(self) -> StarRailYOLO:
        if self._sim_uni_yolo is None:
            model_name = self.one_dragon_config.sim_uni_yolo
            self._sim_uni_yolo = StarRailYOLO(
                model_parent_dir_path=get_yolo_model_parent_dir(),
                model_name=model_name
            )
            log.info('加载YOLO识别器完毕')

        return self._sim_uni_yolo


def get_game_win() -> Window:
    return Window(gt('崩坏：星穹铁道', model='ui'))


_ocr_matcher = {}


def get_ocr_matcher(lang: str) -> OcrMatcher:
    matcher: Optional[OcrMatcher] = None
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


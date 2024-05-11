import os
import shutil
from typing import List, Optional

from basic import os_utils
from basic.config import ConfigHolder


class OneDragonAccount:

    def __init__(self, idx: int, name: str, active: bool, active_in_od: bool):
        self.idx: int = idx
        self.name: str = name
        self.active: bool = active
        self.active_in_od: bool = active_in_od


class ProxyType:

    def __init__(self, id: str, cn: str):
        """
        代理类型
        """
        self.id = id
        """唯一标识"""
        self.cn = cn
        """代理类型名称"""


PROXY_TYPE_NONE = ProxyType(id='none', cn='无')
PROXY_TYPE_PERSONAL = ProxyType(id='personal', cn='个人代理')
PROXY_TYPE_GHPROXY = ProxyType(id='ghproxy', cn='免费代理')
PROXY_TYPE_LIST: List[ProxyType] = [PROXY_TYPE_NONE, PROXY_TYPE_PERSONAL, PROXY_TYPE_GHPROXY]
GH_PROXY_URL = 'https://mirror.ghproxy.com/'


class OneDragonConfig(ConfigHolder):

    def __init__(self):
        self.account_list: List[OneDragonAccount] = []
        ConfigHolder.__init__(self, 'one_dragon', sample=False)

    def _init_after_read_file(self):
        self._init_account_list()

    def _init_account_list(self):
        """
        初始化账号列表
        :return:
        """
        account_list = self.dict_account_list

        self.account_list.clear()
        for account in account_list:
            self.account_list.append(OneDragonAccount(**account))

    def create_new_account(self, first: bool) -> OneDragonAccount:
        """
        创建一个新的脚本账号
        :param first:
        :return:
        """
        idx = 0
        while True:
            idx += 1
            existed: bool = False
            for account in self.account_list:
                if account.idx == idx:
                    existed = True
                    break
            if not existed:
                break

        new_account = OneDragonAccount(idx, '账号%02d' % idx, first, True)
        self.account_list.append(new_account)

        dict_account_list = self.dict_account_list
        dict_account_list.append(vars(new_account))
        self.dict_account_list = dict_account_list

        return new_account

    def update_account(self, to_update: OneDragonAccount):
        """
        更新一个账号
        :param to_update:
        :return:
        """
        dict_account_list = self.dict_account_list

        for account in dict_account_list:
            if account['idx'] == to_update.idx:
                account['name'] = to_update.name
                account['active_in_od'] = to_update.active_in_od

        self.save()
        self._init_account_list()

    def active_account(self, account_idx: int):
        """
        启用一个账号
        :param account_idx:
        :return:
        """
        dict_account_list = self.dict_account_list

        for account in dict_account_list:
            account['active'] = account['idx'] == account_idx

        self.save()
        self._init_account_list()

    def delete_account(self, account_idx: int):
        """
        删除一个账号
        :param account_idx:
        :return:
        """
        idx = -1

        dict_account_list = self.dict_account_list
        for i in range(len(dict_account_list)):
            if dict_account_list[i]['idx'] == account_idx:
                idx = i
                break
        if idx != -1:
            dict_account_list.pop(idx)
        self.dict_account_list = dict_account_list

        account_dir = os_utils.get_path_under_work_dir('config', ('%02d' % account_idx))
        if os.path.exists(account_dir):
            shutil.rmtree(account_dir)

        self.save()
        self._init_account_list()

    @property
    def dict_account_list(self) -> List[dict]:
        return self.get('account_list', [])

    @dict_account_list.setter
    def dict_account_list(self, new_list: List[dict]):
        self.update('account_list', new_list)

    @property
    def current_active_account(self) -> Optional[OneDragonAccount]:
        """
        获取当前激活使用的账号
        :return:
        """
        for account in self.account_list:
            if account.active:
                return account
        return None

    @property
    def is_debug(self) -> bool:
        """
        调试模式
        :return:
        """
        return self.get('is_debug', False)

    @is_debug.setter
    def is_debug(self, new_value: bool):
        """
        更新调试模式
        :return:
        """
        self.update('is_debug', new_value)

    @property
    def proxy_type(self) -> str:
        """
        代理类型
        :return:
        """
        return self.get('proxy_type', 'ghproxy')

    @proxy_type.setter
    def proxy_type(self, new_value: str):
        """
        更新代理类型
        :return:
        """
        self.update('proxy_type', new_value)

    @property
    def personal_proxy(self) -> str:
        """
        代理类型
        :return:
        """
        return self.get('personal_proxy', '')

    @personal_proxy.setter
    def personal_proxy(self, new_value: str):
        """
        更新代理类型
        :return:
        """
        self.update('personal_proxy', new_value)


    @property
    def proxy_address(self) -> Optional[str]:
        """
        :return: 真正使用的代理地址
        """
        proxy_type = self.proxy_type
        if proxy_type == PROXY_TYPE_NONE.id:
            return None
        elif proxy_type == PROXY_TYPE_GHPROXY.id:
            return GH_PROXY_URL
        elif proxy_type == PROXY_TYPE_PERSONAL.id:
            proxy = self.personal_proxy
            return None if proxy == '' else proxy
        return None

    @property
    def screen_sim_uni_route(self) -> List[str]:
        """
        完成了截图的模拟宇宙路线
        :return:
        """
        return self.get('screen_sim_uni_route', [])

    def add_screen_sim_uni_route(self, route_id: str):
        """
        增加完成了截图的模拟宇宙路线
        :param route_id:
        :return:
        """
        old_list = self.screen_sim_uni_route
        old_list.append(route_id)
        self.update('screen_sim_uni_route', old_list)

    @property
    def sim_uni_yolo(self) -> str:
        return self.get('sim_uni_yolo', 'yolov8n-640-simuni')

    @sim_uni_yolo.setter
    def sim_uni_yolo(self, new_value: str):
        self.update('sim_uni_yolo', new_value)

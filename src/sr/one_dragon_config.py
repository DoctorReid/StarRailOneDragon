from typing import List, Optional

from basic.config import ConfigHolder


class OneDragonAccount:

    def __init__(self, idx: int, name: str, active: bool, active_in_od: bool):
        self.idx: int = idx
        self.name: str = name
        self.active: bool = active
        self.active_in_od: bool = active_in_od


class OneDragonConfig(ConfigHolder):

    def __init__(self):
        self.account_list: List[OneDragonAccount] = []
        ConfigHolder.__init__(self, 'script_account', sample=False)

    def _init_after_read_file(self):
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

        new_account = OneDragonAccount(idx, '账号%02d' % idx, first, False)
        self.account_list.append(new_account)

        dict_account_list = self.dict_account_list
        dict_account_list.append(vars(new_account))
        self.dict_account_list = dict_account_list

        return new_account

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

import os

import yaml

from one_dragon.utils import os_utils
from sr_od.app.div_uni.entity.div_uni_bless import DivUniBless
from sr_od.app.div_uni.entity.div_uni_curio import DivUniCurio
from sr_od.app.div_uni.entity.div_uni_equation import DivUniEquation


class DivUniDataService:

    def __init__(self):
        self.curio_list: list[DivUniCurio] = []
        self.equation_list: list[DivUniEquation] = []
        self.bless_list: list[DivUniBless] = []

    def load_all(self):
        self.load_curio_list()
        self.load_equation_list()
        self.load_bless_list()

    def load_curio_list(self) -> None:
        """
        加载奇物列表
        """
        save_file_path = os.path.join(
            os_utils.get_path_under_work_dir('assets', 'game_data', 'div_uni'),
            'div_uni_curio.yml'
        )

        with open(save_file_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
            self.curio_list = [
                DivUniCurio(
                    **i
                )
                for i in data
            ]

    def load_equation_list(self) -> None:
        """
        加载方程列表
        """
        save_file_path = os.path.join(
            os_utils.get_path_under_work_dir('assets', 'game_data', 'div_uni'),
            'div_uni_equation.yml'
        )

        with open(save_file_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
            self.equation_list = [
                DivUniEquation(
                    **i
                )
                for i in data
            ]

    def load_bless_list(self) -> None:
        """
        加载祝福列表
        """
        self.bless_list.clear()
        for file_name in ['div_uni_bless.yml', 'div_uni_bless_others.yml']:
            save_file_path = os.path.join(
                os_utils.get_path_under_work_dir('assets', 'game_data', 'div_uni'),
                file_name
            )

            with open(save_file_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
                self.bless_list.extend([
                    DivUniBless(
                        **i
                    )
                    for i in data
                ])


def __debug():
    service = DivUniDataService()
    service.load_all()
    print(len(service.curio_list))
    print(len(service.equation_list))
    print(len(service.bless_list))


if __name__ == '__main__':
    __debug()
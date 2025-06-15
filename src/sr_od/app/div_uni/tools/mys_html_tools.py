import os
import re

import yaml
from bs4 import BeautifulSoup
from one_dragon.utils import os_utils
from sr_od.app.div_uni.entity.div_uni_bless import DivUniBless
from sr_od.app.div_uni.entity.div_uni_curio import DivUniCurio
from sr_od.app.div_uni.entity.div_uni_equation import DivUniEquation


def read_mys_file(filename: str) -> str:
    """
    读取一个mys文件夹下的文件 返回里面的内容
    """
    filepath = os.path.join(
        os_utils.get_path_under_work_dir('.debug', 'mys'),
        filename
    )

    # 使用 with 语句自动处理文件关闭
    with open(filepath, 'r', encoding='utf-8') as file:
        content = file.read()

    return content


def extract_div_uni_curio(filename: str) -> list[DivUniCurio]:
    """
    从html文件中 解析奇物
    """
    html_content = read_mys_file(filename)
    soup = BeautifulSoup(html_content, 'html.parser')

    category_list = [
        ('加权奇物一览', '', '奇物', 4),
        ('奇物一览', '3星奇物', '奇物', 3),
        ('奇物一览', '2星奇物', '奇物', 2),
        ('奇物一览', '1星奇物', '奇物', 1),
        ('奇物一览', '负面奇物', '奇物', 0),
    ]
    h2_list = [i[0] for i in category_list]
    # 先找到各个等级的奇物标题
    target_h2_list = soup.find_all('h2', string=h2_list)  # 精确匹配文本

    current_h2: str = category_list[0][0]
    current_h3: str = category_list[0][1]
    level_div_map: dict[int, list] = {}

    # 获取 h2 同级的div块
    current_element = target_h2_list[0]
    while True:
        current_element = current_element.find_next_sibling()
        if current_element is None:
            break

        if current_element.name == 'h2':
            current_h2 = current_element.text
        elif current_element.name == 'h3':
            current_h3 = current_element.text
        else:
            for category in category_list:
                level = category[3]
                if level not in level_div_map:
                    level_div_map[level] = []
                if category[0] == current_h2 and category[1] == current_h3:
                    level_div_map[level].append(current_element)
                    break

    curio_list: list[DivUniCurio] = []
    for category in category_list:
        level = category[3]
        div_list = level_div_map[level]
        for div in div_list:
            # 查找所有符合条件的td标签
            td_elements = div.find_all('td')
            for td in td_elements:
                # 检查是否包含label和span的结构
                label = td.find('label', string='奇物名称：')
                if label is None:
                    continue
                span = label.find_next_sibling('span')
                if span is None:
                    continue
                curio_name = span.text
                curio = DivUniCurio(
                    category=category[2],
                    level=level,
                    name=curio_name,
                )
                print('识别奇物: ', curio.category, ' ', level, ' ', curio_name)
                curio_list.append(curio)

    print('总共奇物数量: ', len(curio_list))

    save_file_path = os.path.join(
        os_utils.get_path_under_work_dir('assets', 'game_data', 'div_uni'),
        'div_uni_curio.yml'
    )

    with open(save_file_path, 'w', encoding='utf-8') as file:
        to_save_list = [i.to_dict() for i in curio_list]
        yaml.dump(to_save_list, file, allow_unicode=True, sort_keys=False)

    return curio_list

def extract_div_uni_equation(filename: str) -> list[DivUniEquation]:
    """
    从html文件中 解析方程
    """
    equation_list: list[DivUniEquation] = []

    html_content = read_mys_file(filename)
    soup = BeautifulSoup(html_content, 'html.parser')

    target_h2_list = soup.find_all('h2', string='方程一览')  # 精确匹配文本

    # 找到同级下第1个ul 是分类
    current_element = target_h2_list[0]
    current_element = current_element.find_next_sibling()
    if current_element is None or current_element.name != 'ul':
        print('未发现分类ul块')
        return equation_list

    category_list: list[str] = []
    # 提取ul中所有li的文本
    for li in current_element.find_all('li'):
        category = li.text
        # 去除category多余字符
        category_list.append(trim_text(category))

    print('识别方程分类: ', category_list)

    # 找到同级下第2个ul 是具体方程
    current_element = current_element.find_next_sibling()
    if current_element is None or current_element.name != 'ul':
        print('未发现方程ul块')
        return equation_list

    for idx, li in enumerate(current_element.find_all('li')):
        category = category_list[idx]
        t_body = li.find('tbody')
        for tr in t_body.find_all('tr'):
            td_list = tr.find_all('td')
            if len(td_list) < 2:
                continue

            name_p = td_list[0].find('p')
            if name_p is None:
                continue
            name = trim_text(name_p.text)

            path_p = td_list[1].find('p')
            if path_p is None:
                continue

            # 判断path_p中是否有 </br>
            if path_p.find('br') is not None:
                # 获取 </br> 前后的文本
                path_1 = path_p.contents[0]
                path_2 = path_p.contents[2]
                path = f'{path_1},{path_2}'
            else:
                path = trim_text(path_p.text)

            if name == '方程名称' and path == '达成条件':
                continue

            print('识别方程: ', category, ' ', name, ' ', path)

            path_arr = path.split(',')
            path_name_list = []
            path_cnt_list = []
            for path in path_arr:
                if path.find('*') > -1:
                    path_split = path.split('*')
                    path_name_list.append(path_split[0])
                    path_cnt_list.append(int(path_split[1]))
                else:
                    # 在 path 中找到第一个数字的位置
                    match = re.search(r'\d', path)
                    num_idx = match.start() if match else -1
                    path_name_list.append(path[:num_idx])
                    path_cnt_list.append(int(path[num_idx:]))

            equation_list.append(
                DivUniEquation(
                    category='方程',
                    level=len(category_list) - idx,
                    name=name,
                    path_list=path_name_list,
                    path_cnt_list=path_cnt_list
                )
            )

    print('总共方程数量: ', len(equation_list))

    save_file_path = os.path.join(
        os_utils.get_path_under_work_dir('assets', 'game_data', 'div_uni'),
        'div_uni_equation.yml'
    )

    with open(save_file_path, 'w', encoding='utf-8') as file:
        to_save_list = [i.to_dict() for i in equation_list]
        yaml.dump(to_save_list, file, allow_unicode=True, sort_keys=False)

    return equation_list

def extract_div_uni_bless(filename: str) -> list[DivUniBless]:
    """
    从html文件中 解析祝福
    """
    bless_list: list[DivUniBless] = []
    level_str_map: dict[str, int] = {
        '三星': 3,
        '二星': 2,
        '一星': 1
    }

    html_content = read_mys_file(filename)
    soup = BeautifulSoup(html_content, 'html.parser')

    target_h2_list = soup.find_all('h2', string='千面英雄·祝福一览')  # 精确匹配文本

    # 找到同级下第1个div 是祝福列表
    current_element = target_h2_list[0]
    current_element = current_element.find_next_sibling()
    if current_element is None or current_element.name != 'div':
        print('未发现祝福div块')
        return bless_list

    t_body = current_element.find('tbody')
    if t_body is None:
        print('未发现祝福tbody块')
        return bless_list

    for tr in t_body.find_all('tr'):
        td_list = tr.find_all('td')
        if len(td_list) < 3:
            continue

        name_p = td_list[0].find('p')
        if name_p is None:
            continue
        name = trim_text(name_p.text)

        level_p = td_list[1].find('p')
        if level_p is None:
            continue
        level = level_str_map.get(trim_text(level_p.text), -1)

        path_p = td_list[2].find('p')
        if path_p is None:
            continue
        path = trim_text(path_p.text)

        if name == '祝福' and level == -1 and path == '命途':
            continue

        print('识别祝福: ', path, ' ', level, ' ', name)

        bless_list.append(
            DivUniBless(
                category=path,
                level=level,
                name=name,
            )
        )

    print('总共祝福数量: ', len(bless_list))

    save_file_path = os.path.join(
        os_utils.get_path_under_work_dir('assets', 'game_data', 'div_uni'),
        'div_uni_bless.yml'
    )

    with open(save_file_path, 'w', encoding='utf-8') as file:
        to_save_list = [i.to_dict() for i in bless_list]
        yaml.dump(to_save_list, file, allow_unicode=True, sort_keys=False)

    return bless_list

def trim_text(text: str) -> str:
    return text.replace('\n', '').replace('\r', '').replace('\t', '').strip()


if __name__ == '__main__':
    # https://bbs.mihoyo.com/sr/wiki/content/4993/detail?bbs_presentation_style=no_header
    html_file_name = 'div_uni.htm'
    # extract_div_uni_curio(html_file_name)
    # extract_div_uni_equation(html_file_name)
    extract_div_uni_bless(html_file_name)
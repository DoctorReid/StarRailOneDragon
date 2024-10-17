import os

from one_dragon.utils import os_utils


def convert_2_new_template() -> None:
    """
    转换所有旧模版
    - 重命名所有 origin.png 成 raw.png
    - 删除 gray.png
    - 删除 features.xml
    :return:
    """
    root_dir = os_utils.get_path_under_work_dir('assets', 'template')
    for sub_dir_name in os.listdir(root_dir):
        sub_dir = os.path.join(root_dir, sub_dir_name)
        if not os.path.isdir(sub_dir):
            continue

        for template_dir_name in os.listdir(sub_dir):
            template_dir = os.path.join(sub_dir, template_dir_name)
            if not os.path.isdir(template_dir):
                continue

            origin_file_path = os.path.join(template_dir, 'origin.png')
            if os.path.exists(origin_file_path):
                raw_file_path = os.path.join(template_dir, 'raw.png')
                # 删除原有的 raw.png
                if os.path.exists(raw_file_path):
                    os.remove(raw_file_path)
                # 重命名
                os.rename(origin_file_path, raw_file_path)
                print(f'rename {origin_file_path} to {raw_file_path}')

            gray_file_path = os.path.join(template_dir, 'gray.png')
            if os.path.exists(gray_file_path):
                os.remove(gray_file_path)
                print(f'delete {gray_file_path}')

            features_file_path = os.path.join(template_dir, 'features.xml')
            if os.path.exists(features_file_path):
                os.remove(features_file_path)
                print(f'delete {features_file_path}')


def convert_2_new_large_map() -> None:
    """
    转换所有旧的模版 大地图部分
    - 重命名所有 origin.png 成 raw.png
    - 删除 gray.png
    - 删除 features.xml
    :return:
    """
    root_dir = os_utils.get_path_under_work_dir('assets', 'template', 'large_map')
    for planet_dir_name in os.listdir(root_dir):
        planet_dir = os.path.join(root_dir, planet_dir_name)
        if not os.path.isdir(planet_dir):
            continue

        for region_dir_name in os.listdir(planet_dir):
            region_dir = os.path.join(planet_dir, region_dir_name)
            if not os.path.isdir(region_dir):
                continue

            origin_file_path = os.path.join(region_dir, 'origin.png')
            if os.path.exists(origin_file_path):
                raw_file_path = os.path.join(region_dir, 'raw.png')
                # 删除原有的 raw.png
                if os.path.exists(raw_file_path):
                    os.remove(raw_file_path)
                # 重命名
                os.rename(origin_file_path, raw_file_path)
                print(f'rename {origin_file_path} to {raw_file_path}')

            gray_file_path = os.path.join(region_dir, 'gray.png')
            if os.path.exists(gray_file_path):
                os.remove(gray_file_path)
                print(f'delete {gray_file_path}')

            features_file_path = os.path.join(region_dir, 'features.xml')
            if os.path.exists(features_file_path):
                os.remove(features_file_path)
                print(f'delete {features_file_path}')


if __name__ == '__main__':
    convert_2_new_template()
    convert_2_new_large_map()

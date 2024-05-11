from basic import os_utils


def get_yolo_model_parent_dir() -> str:
    return os_utils.get_path_under_work_dir('model', 'yolo')

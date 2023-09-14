import cv2
from PIL.Image import Image

from basic.img import ImageMatcher, MatchResult, cv2_utils
from basic.log_utils import log


def cut_little_map(screen: cv2.typing.MatLike):
    """
    从整个游戏窗口截图中 裁剪出小地图部分
    :param screen:
    :return:
    """
    x, y = 60, 110  # 小地图坐标
    x2, y2 = 240, 280
    return screen[y:y2, x:x2]


def cut_little_map_arrow(screen: cv2.typing.MatLike):
    """
    从整个游戏窗口截图中 裁剪出小地图里的方向箭头
    :param screen:
    :return:
    """
    x, y = 130, 180  # 箭头坐标
    x2, y2 = 170, 220
    return screen[y:y2, x:x2]


def get_direction_by_screenshot(screen: Image, matcher: ImageMatcher, threshold: float = 0.5,
                                show_match_result: bool = False) -> int:
    """
    在整个游戏窗口的截图中，找到小地图部分，通过匹配箭头判断当前方向。
    使用前需要先按一次w前进 确保人物方向与视角朝向一致
    :param screen: 全屏截图
    :param matcher: 图片匹配器
    :param threshold: 阈值
    :param show_match_result 显示匹配结果
    :return: 当前方向
    """
    little_map = cut_little_map_arrow(screen)
    angle_result = matcher.match_template_with_rotation(little_map, 'loc_arrow', threshold)
    target: MatchResult = None
    angle: int = None
    for k, v in angle_result.items():
        for r in v:
            if target is None or r.confidence > target.confidence:
                target = r
                angle = k

    log.debug('当前小地图匹配方向 %d 置信度 %.2f' % (angle, target.confidence) if angle is not None else '当前小地图未匹配到方向')
    if show_match_result:
        cv2_utils.show_image(little_map, target)

    return angle

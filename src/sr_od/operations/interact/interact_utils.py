from cv2.typing import MatLike
from typing import Optional, List

from one_dragon.base.matcher.match_result import MatchResult
from one_dragon.utils import str_utils, cv2_utils
from one_dragon.utils.i18_utils import gt
from sr_od.context.sr_context import SrContext


def check_move_interact(ctx: SrContext, screen: MatLike, cn: str,
                        single_line: bool = False, lcs_percent: float = 0.1) -> Optional[MatchResult]:
    """
    在画面上识别是否有可交互的文本
    :param ctx: 上下文
    :param screen: 游戏画面截图
    :param cn: 需要识别的中文交互文本
    :param single_line: 是否只有单行
    :param lcs_percent: 文本匹配阈值
    :return: 返回文本位置
    """
    words = get_move_interact_words(ctx, screen, single_line=single_line)
    for word in words:
        if str_utils.find_by_lcs(word.data, gt(cn, 'ocr'), percent=lcs_percent):
            return word
    return None


def get_move_interact_words(ctx: SrContext, screen: MatLike, single_line: bool = False) -> List[MatchResult]:
    """
    获取交互文本
    :param ctx:
    :param screen:
    :param single_line:
    :return:
    """
    if single_line:
        area = ctx.screen_loader.get_area('大世界', '移动交互-单行')
    else:
        area = ctx.screen_loader.get_area('大世界', '移动交互-多行')
    part, _ = cv2_utils.crop_image(screen, area.rect)

    if single_line:
        word = ctx.ocr.run_ocr_single_line(part)
        if word is not None:
            return [MatchResult(1, area.rect.x1, area.rect.y1, area.rect.width, area.rect.height, data=word)]
        else:
            return []
    else:
        ocr_result = ctx.ocr.run_ocr(part)
        return [i.max for i in ocr_result.values()]

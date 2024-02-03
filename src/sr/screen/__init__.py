from typing import Optional

from basic import Rect


class ScreenArea:

    def __init__(self,
                 pc_rect: Rect,
                 text: Optional[str] = None,
                 lcs_percent: float = 0.1,
                 template_id: Optional[str] = None,
                 template_sub_dir: Optional[str] = None):
        self.pc_rect: Rect = pc_rect
        self.text: Optional[str] = text
        self.lcs_percent: float = lcs_percent
        self.template_id: Optional[str] = template_id
        self.template_sub_dir: Optional[str] = template_sub_dir

    @property
    def rect(self) -> Rect:
        return self.pc_rect

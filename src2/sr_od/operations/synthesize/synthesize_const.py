from enum import Enum


class SynthesizeItem:

    def __init__(self, category: str, name: str, template_id: str):
        self.category: str = category
        self.name: str = name
        self.template_id: str = template_id


class SynthesizeItemEnum(Enum):

    TRICK_SNACK = SynthesizeItem('消耗品合成', '奇巧零食', 'trick_snack')

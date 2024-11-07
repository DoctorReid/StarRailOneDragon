from enum import Enum


class OpEnum(Enum):

    BACK_TO_WORLD_PLUS = 'back_to_world_plus'
    TRANSPORT = 'transport'
    WAIT = 'wait'
    MOVE = 'move'
    SLOW_MOVE = 'slow_move'
    PATROL = 'patrol'
    INTERACT = 'interact'
    CLICK = 'click'
    BUY_STORE_ITEM = 'buy_store_item'
    SYNTHESIZE = 'synthesize'


class OpWaitTypeEnum(Enum):

    IN_WORLD = 'in_world'
    SECONDS = 'seconds'


class OpInteractTypeEnum(Enum):

    WORLD = 'world'
    WORLD_SINGLE_LINE = 'world_single_line'
    TALK = 'talk'

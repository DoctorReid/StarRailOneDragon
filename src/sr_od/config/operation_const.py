OP_MOVE = 'move'  # 正常移动
OP_SLOW_MOVE = 'slow_move'  # 不使用疾跑的移动
OP_NO_POS_MOVE = 'no_pos_move'  # 不使用疾跑的移动 且不判断坐标 固定按键移动。用于难以判断坐标的情况
OP_PATROL = 'patrol'
OP_CATAPULT = 'catapult'
OP_DISPOSABLE = 'disposable'
OP_INTERACT = 'interact'
OP_WAIT = 'wait'
OP_UPDATE_POS = 'update_pos'
OP_ENTER_SUB = 'enter_sub'

# 等待类型
WAIT_TYPE_IN_WORLD = 'in_world'
WAIT_TYPE_SECONDS = 'seconds'
WAIT_TYPE_OPTS = {
    '主界面': WAIT_TYPE_IN_WORLD,
    '秒数': 'seconds'
}

from basic.img.os import get_test_image
from sr.context.context import get_context
from sr.operation.unit.interact import Interact

if __name__ == '__main__':
    ctx = get_context()
    ctx.running = True
    op = Interact(ctx, '装置')
    screen = get_test_image('f', sub_dir='main')
    op.check_on_screen(screen)
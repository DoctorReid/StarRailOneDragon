from basic.img.os import get_test_image
from sr.context import get_context
from sr.operation.unit.interactive import Interactive

if __name__ == '__main__':
    ctx = get_context()
    ctx.running = True
    op = Interactive(ctx, '装置', wait=0)
    screen = get_test_image('f', sub_dir='main')
    op.check_on_screen(screen)
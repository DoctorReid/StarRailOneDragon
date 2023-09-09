# https://github.com/pywinauto/pywinauto


from pywinauto import Application, findwindows, WindowNotFoundError


def find_app_by_name(window_name: str) -> Application:
    """
    根据名称找到具体的窗口 需完全相等
    :param window_name: 窗口名称
    :return: Application
    :raise WindowNotFoundError
    """
    handle = findwindows.find_window(title=window_name)
    return Application(backend='uia').connect(handle=handle)


def switch_to_app(app: Application):
    """
    切换到具体的应用上 不会改变最顶层窗口
    :param app: 应用
    :return: None
    :raise WindowNotFoundError 找不到对应窗口
    """
    if app is None:
        raise WindowNotFoundError
    app.top_window().set_focus()

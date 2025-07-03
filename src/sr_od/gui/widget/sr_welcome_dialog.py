from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QHBoxLayout, QSpacerItem, QSizePolicy
from qfluentwidgets import PushButton
from one_dragon_qt.widgets.welcome_dialog import WelcomeDialog


class SrWelcomeDialog(WelcomeDialog):
    """自定义欢迎对话框，继承自 WelcomeDialog"""

    def __init__(self, parent=None):
        WelcomeDialog.__init__(self, parent, title="欢迎使用星穹铁道一条龙")

    def _setup_buttons(self):
        """设置对话框按钮"""
        quick_start_button = PushButton("快速开始", self)
        quick_start_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://onedragon-anything.github.io/sr/zh/quickstart.html")))
        quick_start_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        quick_start_button.adjustSize()

        github_button = PushButton("开源地址", self)
        github_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/DoctorReid/StarRailOneDragon")))
        github_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        github_button.adjustSize()

        spacer = QSpacerItem(10, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(quick_start_button)
        button_layout.addItem(spacer)
        button_layout.addWidget(github_button)
        button_layout.addStretch(1)
        self.viewLayout.addLayout(button_layout)
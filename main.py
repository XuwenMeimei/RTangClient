import sys
import time
import os  # 新增
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QProgressBar
)
from PySide6.QtGui import QPixmap, QFont, QMouseEvent, QGuiApplication
from PySide6.QtCore import Qt, QPoint, QTimer, QPropertyAnimation, QEasingCurve


# 新增：统一资源路径获取函数
def resource_path(relative_path):
    """获取资源文件的绝对路径，兼容PyInstaller打包和源码运行"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class RTangClient(QWidget):
    SIDEBAR_WIDTH = 220
    BUTTON_WIDTH = 180
    BUTTON_HEIGHT = 45
    TOAST_WIDTH = 200
    TOAST_HEIGHT = 40
    TOAST_MARGIN = 20

    def __init__(self):
        super().__init__()
        self.setWindowTitle("RTangClient")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._old_pos = None
        self._active_toasts = []
        self.calculate_window_size()
        self.init_ui()

    def calculate_window_size(self):
        screen = QGuiApplication.primaryScreen().availableGeometry()
        screen_width, screen_height = screen.width(), screen.height()

        window_width = int(screen_width * 0.75)
        window_height = int(window_width * 9 / 16)

        if window_height > screen_height * 0.9:
            window_height = int(screen_height * 0.9)
            window_width = int(window_height * 16 / 9)

        self.resize(window_width, window_height)
        self.move(
            (screen_width - window_width) // 2,
            (screen_height - window_height) // 2
        )

    def init_ui(self):
        self.init_toast_label()
        self.init_background()
        self.init_main_layout()

    def init_toast_label(self):
        self.toast_label = QLabel("", self)
        self.toast_label.setObjectName("toastLabel")
        self.toast_label.setAlignment(Qt.AlignCenter)
        self.toast_label.setFixedHeight(self.TOAST_HEIGHT)
        self.toast_label.setFixedWidth(self.TOAST_WIDTH)
        self.toast_label.hide()
        self.toast_label.setAttribute(Qt.WA_StyledBackground, True)

    def init_background(self):
        self.background = QFrame(self)
        self.background.setObjectName("background")
        self.background.setGeometry(0, 0, self.width(), self.height())

    def init_main_layout(self):
        main_layout = QVBoxLayout(self.background)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.init_title_bar(main_layout)
        self.init_content(main_layout)

    def init_title_bar(self, main_layout):
        self.title_bar = QFrame()
        self.title_bar.setObjectName("titleBar")
        self.title_bar.setFixedHeight(32)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)

        title_label = QLabel("RTangClient")
        title_label.setObjectName("titleLabel")
        title_label.setFont(QFont("Microsoft YaHei", 10))

        minimize_button = QPushButton("➖")
        minimize_button.setObjectName("titleButton")
        minimize_button.clicked.connect(self.showMinimized)

        close_button = QPushButton("❌")
        close_button.setObjectName("titleButton")
        close_button.clicked.connect(self.close)

        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(minimize_button)
        title_layout.addWidget(close_button)
        main_layout.addWidget(self.title_bar)

    def init_content(self, main_layout):
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        self.init_sidebar(content_layout)
        self.init_main_content(content_layout)
        main_layout.addLayout(content_layout)

    def init_sidebar(self, content_layout):
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(self.SIDEBAR_WIDTH)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(20, 30, 20, 30)
        sidebar_layout.setSpacing(20)
        sidebar_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        self.start_button = QPushButton("启动游戏")
        self.start_button.setObjectName("startButton")
        self.start_button.setFixedWidth(self.BUTTON_WIDTH)
        self.start_button.setFixedHeight(self.BUTTON_HEIGHT)
        self.start_button.clicked.connect(self.start_game)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setFixedWidth(self.BUTTON_WIDTH)
        self.progress_bar.setFixedHeight(self.BUTTON_HEIGHT)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()

        sidebar_layout.addWidget(self.start_button)
        sidebar_layout.addWidget(self.progress_bar)
        sidebar_layout.addStretch()
        content_layout.addWidget(self.sidebar)

    def init_main_content(self, content_layout):
        self.content = QFrame()
        self.content.setObjectName("content")
        content_v_layout = QVBoxLayout(self.content)
        content_v_layout.setContentsMargins(0, 0, 0, 0)
        content_v_layout.setSpacing(20)
        content_v_layout.setAlignment(Qt.AlignCenter)

        self.logo = QLabel()
        pixmap = QPixmap(resource_path("assets/logo.png"))
        if pixmap.isNull():
            self.logo.setText("[Logo]")
            QTimer.singleShot(0, lambda: self.show_toast("Logo 加载失败！"))
        else:
            self.logo.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.logo.setAlignment(Qt.AlignCenter)
        self.logo.hide()  # 隐藏logo

        self.status_label = QLabel("未登录")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setFont(QFont("Microsoft YaHei", 16))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.hide()  # 隐藏未登录

        content_v_layout.addWidget(self.logo)
        content_v_layout.addWidget(self.status_label)
        content_v_layout.addStretch()
        content_layout.addWidget(self.content)

    def start_game(self):
        self.start_button.setEnabled(False)
        self.start_button.setText("游戏启动中...")

        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.progress_bar.raise_()
        self.progress_bar.move(self.start_button.pos())
        self.progress_bar.resize(self.start_button.size())
        self.progress_bar.show()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(10)

    def update_progress(self):
        value = self.progress_bar.value()
        if value < 100:
            self.progress_bar.setValue(value + 5)
        else:
            self.timer.stop()
            self.progress_bar.hide()
            self.start_button.setText("启动游戏")
            self.start_button.setEnabled(True)
            self.show_toast("启动完成！")  # 传入提示文本

    def show_toast(self, message):
        MAX_TOASTS = 5  # 最多同时显示5个toast
        margin = 20
        spacing = 10
        toast_height = 40

        # 超过最大数量，先移除最早的toast
        while len(self._active_toasts) >= MAX_TOASTS:
            old_toast = self._active_toasts.pop(-1)  # 移除队列最后一个
            old_toast.hide()
            old_toast.deleteLater()

        toast = QLabel(message, self)
        toast.setObjectName("toastLabel")
        toast.setAlignment(Qt.AlignCenter)
        toast.setFixedHeight(toast_height)
        toast.adjustSize()
        toast.setAttribute(Qt.WA_StyledBackground, True)
        toast.setWindowOpacity(1.0)
        toast.raise_()

        start_x = self.width() - toast.width() - margin
        start_y = self.height() - toast.height() - margin

        # 先把已有的toast全部向上移动一格
        for idx, t in enumerate(self._active_toasts):
            target_y = self.height() - t.height() - margin - (idx + 1) * (t.height() + spacing)
            anim = QPropertyAnimation(t, b"pos", t)
            anim.setDuration(200)
            anim.setStartValue(t.pos())
            anim.setEndValue(QPoint(start_x, target_y))
            anim.setEasingCurve(QEasingCurve.OutQuad)
            t._move_anim = anim  # 强引用
            anim.start()

        toast.move(start_x, start_y + 60)
        toast.show()
        self._active_toasts.insert(0, toast)

        # 保证动画对象和toast生命周期一致
        anim_show = QPropertyAnimation(toast, b"pos", toast)
        anim_show.setDuration(300)
        anim_show.setStartValue(QPoint(start_x, start_y + 60))
        anim_show.setEndValue(QPoint(start_x, start_y))
        anim_show.setEasingCurve(QEasingCurve.OutQuad)
        toast._anim_show = anim_show  # 强引用
        anim_show.start()

        def fade_out_toast():
            if getattr(toast, "_is_fading", False):
                return
            toast._is_fading = True
            anim_fade = QPropertyAnimation(toast, b"windowOpacity", toast)
            anim_fade.setDuration(600)
            anim_fade.setStartValue(1.0)
            anim_fade.setEndValue(0.0)
            anim_fade.setEasingCurve(QEasingCurve.InQuad)
            toast._anim_fade = anim_fade  # 强引用

            def on_finished():
                toast.hide()
                toast.deleteLater()
                if toast in self._active_toasts:
                    self._active_toasts.remove(toast)
                # 重新排列剩余的toast
                for idx, t in enumerate(self._active_toasts):
                    target_y = self.height() - t.height() - margin - idx * (t.height() + spacing)
                    if t.pos().y() != target_y:
                        anim = QPropertyAnimation(t, b"pos", t)
                        anim.setDuration(200)
                        anim.setStartValue(t.pos())
                        anim.setEndValue(QPoint(start_x, target_y))
                        anim.setEasingCurve(QEasingCurve.OutQuad)
                        t._move_anim = anim
                        anim.start()

            anim_fade.finished.connect(on_finished)
            anim_fade.start()

        # 动画结束后延时消失
        def stay_and_hide():
            QTimer.singleShot(2000, fade_out_toast)

        anim_show.finished.connect(stay_and_hide)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and self.title_bar.geometry().contains(event.position().toPoint()):
            self._old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._old_pos:
            delta = event.globalPosition().toPoint() - self._old_pos
            self.move(self.pos() + delta)
            self._old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._old_pos = None


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 统一加载外部 qss 样式文件，使用 resource_path
    try:
        with open(resource_path("styles/pink_theme.qss"), "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print("Warning: styles/pink_theme.qss not found, running without style.")

    win = RTangClient()
    win.show()
    sys.exit(app.exec())

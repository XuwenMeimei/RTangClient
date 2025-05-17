import sys
import os  # 新增
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QProgressBar, QGraphicsOpacityEffect, QFileDialog
)
from PySide6.QtGui import QPixmap, QFont, QMouseEvent, QGuiApplication, QFontMetrics, QPainter
from PySide6.QtCore import Qt, QPoint, QTimer, QPropertyAnimation, QParallelAnimationGroup, QEasingCurve, QRect, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput


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
    TOAST_ANIM_DURATION = 300
    TOAST_FADE_DURATION = 300
    TOAST_LIFETIME = 5000
    TOAST_SPACING = 10
    MAX_TOASTS = 10

    def __init__(self):
        super().__init__()
        self.setWindowTitle("RTangClient")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._old_pos = None
        self._active_toasts = []
        self.calculate_window_size()

        # 音乐相关初始化提前
        self.music_files = []
        self.music_index = -1
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)

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
        self.init_music_controls(main_layout)  # 新增

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
        sidebar_layout.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)  # 关键：底部对齐

        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)

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

        btn_layout.addWidget(self.start_button)
        btn_layout.addWidget(self.progress_bar)

        # 保证sidebar_layout只加btn_layout
        sidebar_layout.addLayout(btn_layout)

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

    def init_music_controls(self, main_layout=None):
        # 音乐播放器控件
        music_bar = QFrame()
        music_bar.setObjectName("musicBar")
        music_layout = QHBoxLayout(music_bar)
        music_layout.setContentsMargins(20, 5, 20, 5)
        music_layout.setSpacing(10)

        self.btn_select_folder = QPushButton("选择音乐文件夹")
        self.btn_select_folder.clicked.connect(self.select_music_folder)

        self.btn_prev = QPushButton("⏮")
        self.btn_prev.clicked.connect(self.play_prev_music)
        self.btn_prev.setEnabled(False)

        self.btn_play = QPushButton("▶️")
        self.btn_play.clicked.connect(self.toggle_play_pause)
        self.btn_play.setEnabled(False)

        self.btn_next = QPushButton("⏭")
        self.btn_next.clicked.connect(self.play_next_music)
        self.btn_next.setEnabled(False)

        self.music_title = QLabel("未选择音乐")
        self.music_title.setMinimumWidth(120)

        # 新增：进度条
        self.music_progress = QProgressBar()
        self.music_progress.setFixedWidth(120)
        self.music_progress.setRange(0, 100)
        self.music_progress.setValue(0)
        self.music_progress.setTextVisible(False)

        # 新增：音乐动效图标
        self.music_icon = QLabel()
        icon_pixmap = QPixmap(resource_path("assets/music_icon.png"))
        if icon_pixmap.isNull():
            self.music_icon.setText("🎵")
        else:
            self.music_icon.setPixmap(icon_pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.music_icon.setFixedSize(32, 32)
        self.music_icon.setAlignment(Qt.AlignCenter)

        music_layout.addWidget(self.music_icon)
        music_layout.addWidget(self.btn_select_folder)
        music_layout.addWidget(self.btn_prev)
        music_layout.addWidget(self.btn_play)
        music_layout.addWidget(self.btn_next)
        music_layout.addWidget(self.music_title)
        music_layout.addWidget(self.music_progress)
        music_layout.addStretch()

        if main_layout:
            main_layout.addWidget(music_bar)
        self.music_bar = music_bar

        # 新增：进度与动效定时器
        self.music_timer = QTimer(self)
        self.music_timer.timeout.connect(self.update_music_progress)
        self._rotation_angle = 0
        self._icon_animating = False

        # 连接播放器信号
        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)
        self.player.playbackStateChanged.connect(self.on_playback_state_changed)

    def start_game(self):
        self.start_button.setEnabled(False)
        self.start_button.hide()  # 隐藏按钮

        self.progress_bar.setValue(0)
        self.progress_bar.show()  # 显示进度条

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(10)

    def update_progress(self):
        value = self.progress_bar.value()
        if value < 100:
            self.progress_bar.setValue(value + 5)
        else:
            self.timer.stop()
            self.progress_bar.hide()  # 隐藏进度条
            self.start_button.setText("启动游戏")
            self.start_button.setEnabled(True)
            self.start_button.show()  # 恢复按钮显示
            self.show_toast("启动完成！")

    def show_toast(self, message: str):
        margin = self.TOAST_MARGIN
        spacing = self.TOAST_SPACING
        toast_width = 300  # 与QSS一致

        # 用 QFontMetrics 计算实际宽度，超出则加省略号
        font = QFont("Microsoft YaHei", 12)
        metrics = QFontMetrics(font)
        elided_message = metrics.elidedText(message, Qt.ElideRight, toast_width - 30)  # 预留padding

        # 超出最大数量时，优雅淡出最早的toast
        while len(self._active_toasts) >= self.MAX_TOASTS:
            old_toast = self._active_toasts.pop(-1)
            self._fade_out_toast(old_toast, rearrange=True)

        toast = QLabel(elided_message, self)
        toast.setObjectName("toastLabel")
        toast.setAlignment(Qt.AlignCenter)
        toast.setWordWrap(True)
        toast.setFixedWidth(toast_width)
        toast.setFont(font)
        toast.setAttribute(Qt.WA_StyledBackground, True)
        toast.setWindowOpacity(1.0)
        toast.raise_()

        toast.adjustSize()
        toast.setFixedHeight(toast.height())

        start_x = self.width() - toast.width() - margin

        # 计算最大可用y，避免覆盖标题栏
        title_bar_height = self.title_bar.height() if hasattr(self, "title_bar") else 32
        min_y = title_bar_height + margin
        max_y = self.height() - toast.height() - margin
        start_y = max(min_y, max_y)

        # 现有toast全部上移
        for idx, t in enumerate(self._active_toasts):
            target_y = max(
                min_y,
                self.height() - t.height() - margin - (idx + 1) * (t.height() + spacing)
            )
            self._move_toast(t, start_x, target_y)

        toast.move(start_x, start_y + 60)
        toast.show()
        self._active_toasts.insert(0, toast)

        # 入场动画
        self._move_toast(toast, start_x, start_y, duration=self.TOAST_ANIM_DURATION)

        # 定时淡出
        QTimer.singleShot(self.TOAST_LIFETIME, lambda: self._fade_out_toast(toast))

    def _move_toast(self, toast, x, y, duration=200):
        anim = QPropertyAnimation(toast, b"pos", toast)
        anim.setDuration(duration)
        anim.setStartValue(toast.pos())
        anim.setEndValue(QPoint(x, y))
        anim.setEasingCurve(QEasingCurve.OutQuad)
        toast._move_anim = anim  # 强引用防止GC
        anim.start()

    def _fade_out_toast(self, toast, rearrange=False):
        if getattr(toast, "_is_fading", False):
            return
        toast._is_fading = True

        # 先隐藏文字内容
        toast.setText("")

        # 锁定绝对位置，防止布局影响
        toast.setParent(self)
        toast.setGeometry(toast.geometry())

        # 可选：移除阴影和边框，防止缩小时锯齿或残影
        toast.setStyleSheet("border: none; background-color: #FFABC1; border-radius: 12px;")

        # 更快的动画时长
        duration = 250

        # 淡出动画
        effect = QGraphicsOpacityEffect(toast)
        toast.setGraphicsEffect(effect)
        anim_fade = QPropertyAnimation(effect, b"opacity", toast)
        anim_fade.setDuration(duration)
        anim_fade.setStartValue(1.0)
        anim_fade.setEndValue(0.0)
        anim_fade.setEasingCurve(QEasingCurve.OutCubic)

        # 只缩小宽度，高度不变
        start_geom = toast.geometry()
        center = start_geom.center()
        shrink_ratio = 0.5
        end_width = max(1, int(start_geom.width() * shrink_ratio))
        end_height = start_geom.height()  # 高度不变
        end_geom = QRect(
            center.x() - end_width // 2,
            center.y() - end_height // 2,
            end_width,
            end_height
        )
        anim_geom = QPropertyAnimation(toast, b"geometry", toast)
        anim_geom.setDuration(duration)
        anim_geom.setStartValue(start_geom)
        anim_geom.setEndValue(end_geom)
        anim_geom.setEasingCurve(QEasingCurve.OutCubic)

        # 并行动画
        group = QParallelAnimationGroup(toast)
        group.addAnimation(anim_fade)
        group.addAnimation(anim_geom)

        def on_finished():
            toast.hide()
            toast.deleteLater()
            if toast in self._active_toasts:
                self._active_toasts.remove(toast)
            if rearrange:
                self._rearrange_toasts()

        group.finished.connect(on_finished)
        group.start()

    def _rearrange_toasts(self):
        """重新排列剩余toast的位置"""
        margin = self.TOAST_MARGIN
        spacing = self.TOAST_SPACING
        for idx, t in enumerate(self._active_toasts):
            target_y = self.height() - t.height() - margin - idx * (t.height() + spacing)
            self._move_toast(t, self.width() - t.width() - margin, target_y)

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

    def init_music_controls(self, main_layout=None):
        # 音乐播放器控件
        music_bar = QFrame()
        music_bar.setObjectName("musicBar")
        music_layout = QHBoxLayout(music_bar)
        music_layout.setContentsMargins(20, 5, 20, 5)
        music_layout.setSpacing(10)

        self.btn_select_folder = QPushButton("选择音乐文件夹")
        self.btn_select_folder.clicked.connect(self.select_music_folder)

        self.btn_prev = QPushButton("⏮")
        self.btn_prev.clicked.connect(self.play_prev_music)
        self.btn_prev.setEnabled(False)

        self.btn_play = QPushButton("▶️")
        self.btn_play.clicked.connect(self.toggle_play_pause)
        self.btn_play.setEnabled(False)

        self.btn_next = QPushButton("⏭")
        self.btn_next.clicked.connect(self.play_next_music)
        self.btn_next.setEnabled(False)

        self.music_title = QLabel("未选择音乐")
        self.music_title.setMinimumWidth(120)

        # 新增：进度条
        self.music_progress = QProgressBar()
        self.music_progress.setFixedWidth(120)
        self.music_progress.setRange(0, 100)
        self.music_progress.setValue(0)
        self.music_progress.setTextVisible(False)

        # 新增：音乐动效图标
        self.music_icon = QLabel()
        icon_pixmap = QPixmap(resource_path("assets/music_icon.png"))
        if icon_pixmap.isNull():
            self.music_icon.setText("🎵")
        else:
            self.music_icon.setPixmap(icon_pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.music_icon.setFixedSize(32, 32)
        self.music_icon.setAlignment(Qt.AlignCenter)

        music_layout.addWidget(self.music_icon)
        music_layout.addWidget(self.btn_select_folder)
        music_layout.addWidget(self.btn_prev)
        music_layout.addWidget(self.btn_play)
        music_layout.addWidget(self.btn_next)
        music_layout.addWidget(self.music_title)
        music_layout.addWidget(self.music_progress)
        music_layout.addStretch()

        # main_layout 为空时不添加（__init__时调用）
        if main_layout:
            main_layout.addWidget(music_bar)
        self.music_bar = music_bar

        # 新增：进度与动效定时器
        self.music_timer = QTimer(self)
        self.music_timer.timeout.connect(self.update_music_progress)
        self._rotation_angle = 0
        self._icon_animating = False

        # 连接播放器信号
        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)
        self.player.playbackStateChanged.connect(self.on_playback_state_changed)

    def select_music_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择音乐文件夹", os.path.expanduser("~"))
        if folder:
            exts = (".mp3", ".wav", ".ogg", ".flac", ".m4a")
            files = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(exts)]
            if files:
                self.music_files = files
                self.music_index = 0
                self.btn_play.setEnabled(True)
                self.btn_prev.setEnabled(True)
                self.btn_next.setEnabled(True)
                self.play_music(self.music_index)
                self.show_toast(f"已加载 {len(files)} 首音乐")
            else:
                self.music_files = []
                self.music_index = -1
                self.btn_play.setEnabled(False)
                self.btn_prev.setEnabled(False)
                self.btn_next.setEnabled(False)
                self.music_title.setText("未找到音乐文件")
                self.show_toast("未找到音乐文件")
        else:
            self.show_toast("未选择文件夹")

    def play_music(self, index):
        if not self.music_files:
            self.show_toast("请先选择音乐文件夹")
            return
        if index < 0 or index >= len(self.music_files):
            self.show_toast("音乐索引超出范围")
            return
        file = self.music_files[index]
        self.player.setSource(QUrl.fromLocalFile(file))
        self.player.play()
        self.music_index = index
        self.music_title.setText(os.path.basename(file))
        self.btn_play.setText("⏸")
        self.show_toast(f"正在播放: {os.path.basename(file)}")
        self.music_progress.setValue(0)
        self.music_progress.setMaximum(100)
        self.start_music_icon_animation()

    def toggle_play_pause(self):
        if self.player.mediaStatus() == QMediaPlayer.NoMedia:
            self.show_toast("请先选择音乐文件夹")
            return
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.btn_play.setText("▶️")
            self.show_toast("已暂停")
            self.stop_music_icon_animation()
        else:
            self.player.play()
            self.btn_play.setText("⏸")
            self.show_toast("继续播放")
            self.start_music_icon_animation()

    def on_position_changed(self, position):
        # position 单位为毫秒
        duration = self.player.duration()
        if duration > 0:
            percent = int(position * 100 / duration)
            self.music_progress.setValue(percent)
        else:
            self.music_progress.setValue(0)

    def on_duration_changed(self, duration):
        # 可用于重置进度条
        self.music_progress.setValue(0)

    def update_music_progress(self):
        # 旋转音乐图标
        if self._icon_animating:
            self._rotation_angle = (self._rotation_angle + 10) % 360
            self.rotate_music_icon(self._rotation_angle)

    def start_music_icon_animation(self):
        if not self._icon_animating:
            self._icon_animating = True
            self.music_timer.start(50)

    def stop_music_icon_animation(self):
        if self._icon_animating:
            self._icon_animating = False
            self.music_timer.stop()
            self.rotate_music_icon(0)

    def rotate_music_icon(self, angle):
        # 仅对pixmap旋转，emoji不处理
        pixmap = self.music_icon.pixmap()
        if pixmap:
            transform = QPixmap(pixmap.size())
            transform.fill(Qt.transparent)
            painter = QPainter(transform)
            painter.translate(pixmap.width() / 2, pixmap.height() / 2)
            painter.rotate(angle)
            painter.translate(-pixmap.width() / 2, -pixmap.height() / 2)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()
            self.music_icon.setPixmap(transform)

    def on_playback_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.start_music_icon_animation()
        else:
            self.stop_music_icon_animation()

    def _on_media_status_changed(self, status):
        if status == QMediaPlayer.EndOfMedia:
            self.play_next_music()

    def play_prev_music(self):
        if not self.music_files:
            return
        self.music_index = (self.music_index - 1) % len(self.music_files)
        self.play_music(self.music_index)

    def play_next_music(self):
        if not self.music_files:
            return
        self.music_index = (self.music_index + 1) % len(self.music_files)
        self.play_music(self.music_index)

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

    def show_random_toasts():
        # 中英文故事片段库
        story_snippets = [
            "从前有座山，山里有座庙，庙里有个老和尚在给小和尚讲故事。",
            "小明走进了神秘的森林，发现了一只会说话的狐狸。",
            "夜深了，窗外下起了大雨，妈妈给我讲了一个温暖的童话。",
            "小兔子和小熊一起去采蘑菇，结果迷路了。",
            "有一天，乌龟和兔子决定再比一次赛跑。",
            "小猫咪第一次见到雪，高兴地在院子里打滚。",
            "爷爷年轻时曾经救过一只受伤的小鸟。",
            "小朋友们在操场上快乐地放风筝。",
            "月亮悄悄爬上了树梢，星星眨着眼睛看着大地。",
            "小鸭子跟着妈妈学游泳，扑通一声掉进了水里。",
            "冬天到了，雪花像小精灵一样在空中飞舞。",
            "小熊学会了自己做蜂蜜蛋糕，邀请朋友们来品尝。",
            "有一只小狗总是喜欢追着自己的尾巴转圈。",
            "春天来了，花儿都开了，蝴蝶在花间飞舞。",
            "小猴子爬上了最高的树，看见了远处的彩虹。",
            "小朋友们围坐在篝火旁，听老师讲神奇的故事。",
            "小鹿在森林里遇见了新朋友小松鼠。",
            "夜晚的湖面像一面镜子，倒映着满天的星星。",
            "小猪学会了自己整理房间，妈妈夸他长大了。",
            "有一天，小鱼游出了池塘，开始了奇妙的冒险。",
            # 英文句子
            "Once upon a time, there was a mountain, and on the mountain there was a temple.",
            "The little rabbit and the little bear went to pick mushrooms and got lost.",
            "It was a rainy night, and mom told me a warm fairy tale.",
            "The kitten saw snow for the first time and rolled happily in the yard.",
            "Grandpa once saved an injured bird when he was young.",
            "Children are happily flying kites on the playground.",
            "The moon quietly climbed up the treetop, and the stars blinked at the earth.",
            "The little duck followed its mother to learn swimming and fell into the water with a splash.",
            "In winter, snowflakes dance in the air like little elves.",
            "The little bear learned to make honey cake and invited friends to taste it.",
            "A little dog always likes to chase its own tail in circles.",
            "Spring has come, flowers are blooming, and butterflies are flying among the flowers.",
            "The little monkey climbed to the highest tree and saw a rainbow in the distance.",
            "Children sat around the campfire, listening to the teacher tell magical stories.",
            "The little deer met a new friend, the little squirrel, in the forest.",
            "At night, the surface of the lake was like a mirror, reflecting the starry sky.",
            "The little pig learned to tidy up his room, and his mother praised him for growing up.",
            "One day, the little fish swam out of the pond and started a wonderful adventure."
        ]
        for i, snippet in enumerate(story_snippets):
            QTimer.singleShot(i * 400, lambda m=snippet: win.show_toast(m))

    #show_random_toasts()

    sys.exit(app.exec())

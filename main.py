import ctypes
import json
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QTime, Signal
from PySide6.QtGui import QPixmap, QAction
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QMessageBox,
    QSystemTrayIcon,
    QMenu,
    QStyle,
    QComboBox,
    QSpinBox,
    QFormLayout,
)


APP_DIR = Path.home() / "AppData" / "Local" / "AuraDesktop"
SETTINGS_FILE = APP_DIR / "settings.json"


def load_settings():
    try:
        with SETTINGS_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_settings(data):
    APP_DIR.mkdir(parents=True, exist_ok=True)
    temporary_file = SETTINGS_FILE.with_suffix(".tmp")
    with temporary_file.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    temporary_file.replace(SETTINGS_FILE)


class DesktopClock(QWidget):
    def __init__(self, position=None):
        super().__init__()
        self.setWindowTitle("AuraDesktop Clock")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.drag_position = None
        self.desktop_attached = False
        self.setFixedSize(280, 100)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)

        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("""
            color: white;
            font-family: "Segoe UI";
            font-size: 36px;
            font-weight: 600;
            background: transparent;
        """)

        self.date_label = QLabel()
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date_label.setStyleSheet("""
            color: #D1D2E0;
            font-family: "Segoe UI";
            font-size: 12px;
            background: transparent;
        """)

        layout.addWidget(self.time_label)
        layout.addWidget(self.date_label)

        self.setStyleSheet("""
            DesktopClock {
                background-color: rgba(30, 31, 42, 210);
                border: 1px solid rgba(255, 255, 255, 45);
                border-radius: 16px;
            }
        """)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)
        self.update_clock()

        if position and len(position) == 2:
            self.move(int(position[0]), int(position[1]))
        else:
            self.move(50, 50)

    def update_clock(self):
        self.time_label.setText(QTime.currentTime().toString("HH:mm:ss"))
        self.date_label.setText(datetime.now().strftime("%A, %d %B %Y"))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        if self.drag_position is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_position = None

    def attach_to_desktop(self):
        """Best-effort attachment to the Windows desktop WorkerW layer."""
        if sys.platform != "win32":
            return False

        user32 = ctypes.windll.user32
        progman = user32.FindWindowW("Progman", None)
        if not progman:
            return False

        result = ctypes.c_ulong()
        user32.SendMessageTimeoutW(
            progman, 0x052C, 0, 0, 0, 1000, ctypes.byref(result)
        )

        workerw = {"handle": 0}
        callback_type = ctypes.WINFUNCTYPE(
            ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p
        )

        def enum_callback(hwnd, _):
            shell_view = user32.FindWindowExW(hwnd, 0, "SHELLDLL_DefView", None)
            if shell_view:
                workerw["handle"] = user32.FindWindowExW(0, hwnd, "WorkerW", None)
                return False
            return True

        callback = callback_type(enum_callback)
        user32.EnumWindows(callback, 0)
        target = workerw["handle"]
        if not target:
            return False

        hwnd = int(self.winId())
        user32.SetParent(hwnd, target)

        GWL_STYLE = -16
        WS_CHILD = 0x40000000
        WS_POPUP = 0x80000000
        style = user32.GetWindowLongW(hwnd, GWL_STYLE)
        style = (style & ~WS_POPUP) | WS_CHILD
        user32.SetWindowLongW(hwnd, GWL_STYLE, style)
        user32.SetWindowPos(hwnd, 0, 50, 50, 280, 100, 0x0040 | 0x0010)
        self.desktop_attached = True
        return True


class ClockScreensaver(QWidget):
    """Full-screen black clock preview; any key/click or deliberate mouse move exits."""
    finished = Signal()
    def __init__(self, settings=None):
        super().__init__()
        self.settings = settings if isinstance(settings, dict) else {}
        self.setWindowTitle("AuraDesktop Screensaver Preview")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setStyleSheet("background-color: #000000;")
        self.setCursor(Qt.CursorShape.BlankCursor)
        self.setMouseTracking(True)
        self._start_mouse_pos = None
        self._ignore_initial_mouse_move = True

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addStretch(2)

        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("""
            color: #F5F5F7;
            background: transparent;
            font-family: "Segoe UI";
            font-weight: 300;
        """)
        self.apply_clock_style()
        layout.addWidget(self.time_label)

        self.date_label = QLabel()
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date_label.setStyleSheet("""
            color: #A7A7B2;
            background: transparent;
            font-family: "Segoe UI";
            font-size: 24px;
            font-weight: 400;
        """)
        layout.addWidget(self.date_label)
        layout.addStretch(3)

        self.hint_label = QLabel("Press any key or move the mouse to exit")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint_label.setStyleSheet("""
            color: #55555F;
            background: transparent;
            font-family: "Segoe UI";
            font-size: 12px;
        """)
        layout.addWidget(self.hint_label)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)
        self.update_clock()

    def apply_clock_style(self):
        color = self.settings.get("screensaver_clock_color", "#F5F5F7")
        allowed_colors = {"#F5F5F7", "#75D9FF", "#FFC66D", "#A6E3A1", "#CBA6F7"}
        if color not in allowed_colors:
            color = "#F5F5F7"
        size = self.settings.get("screensaver_clock_size", 96)
        try:
            size = max(64, min(160, int(size)))
        except (TypeError, ValueError):
            size = 96
        self.time_label.setStyleSheet(f"""
            color: {color}; background: transparent;
            font-family: "Segoe UI"; font-size: {size}px; font-weight: 300;
        """)

    def update_clock(self):
        time_format = self.settings.get("screensaver_time_format", "24h")
        time_pattern = "hh:mm AP" if time_format == "12h" else "HH:mm"
        self.time_label.setText(QTime.currentTime().toString(time_pattern))
        self.date_label.setText(datetime.now().strftime("%A, %d %B %Y"))

    def show_preview(self):
        self._start_mouse_pos = None
        self._ignore_initial_mouse_move = True
        self.showFullScreen()
        self.activateWindow()
        self.setFocus()
        QTimer.singleShot(700, self._enable_mouse_exit)

    def _enable_mouse_exit(self):
        self._ignore_initial_mouse_move = False
        self._start_mouse_pos = None

    def keyPressEvent(self, event):
        self.close()

    def mousePressEvent(self, event):
        self.close()

    def mouseMoveEvent(self, event):
        if self._ignore_initial_mouse_move:
            return
        pos = event.globalPosition().toPoint()
        if self._start_mouse_pos is None:
            self._start_mouse_pos = pos
            return
        if (pos - self._start_mouse_pos).manhattanLength() >= 12:
            self.close()

    def closeEvent(self, event):
        self.unsetCursor()
        event.accept()
        self.finished.emit()


class AuraDesktop(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AuraDesktop")
        self.resize(900, 650)
        self.setMinimumSize(700, 500)

        self.settings = load_settings()
        self.image_path = None
        self.clock = None
        self._exiting = False

        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        title = QLabel("AuraDesktop")
        title.setObjectName("title")
        subtitle = QLabel("Personalize your Windows desktop.")
        subtitle.setObjectName("subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        section = QLabel("Wallpaper")
        section.setObjectName("section")
        layout.addWidget(section)

        self.preview = QLabel("Choose an image to preview")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumHeight(300)
        self.preview.setObjectName("preview")
        layout.addWidget(self.preview, 1)

        self.path_label = QLabel("No image selected")
        self.path_label.setObjectName("subtitle")
        self.path_label.setWordWrap(True)
        layout.addWidget(self.path_label)

        buttons = QHBoxLayout()
        choose_button = QPushButton("Choose Image")
        choose_button.clicked.connect(self.choose_image)
        self.apply_button = QPushButton("Set as Wallpaper")
        self.apply_button.setObjectName("primary")
        self.apply_button.setEnabled(False)
        self.apply_button.clicked.connect(self.apply_wallpaper)
        buttons.addWidget(choose_button)
        buttons.addWidget(self.apply_button)
        buttons.addStretch()
        layout.addLayout(buttons)

        self.clock_button = QPushButton("Show Desktop Clock")
        self.clock_button.clicked.connect(self.toggle_clock)
        layout.addWidget(self.clock_button)

        self.screensaver_button = QPushButton("Preview Clock Screensaver")
        self.screensaver_button.clicked.connect(self.preview_screensaver)
        layout.addWidget(self.screensaver_button)

        screensaver_options = QFormLayout()
        screensaver_options.setHorizontalSpacing(16)
        screensaver_options.setVerticalSpacing(8)

        self.screensaver_color = QComboBox()
        self._screensaver_colors = {
            "Soft White": "#F5F5F7",
            "Sky Blue": "#75D9FF",
            "Warm Amber": "#FFC66D",
            "Mint Green": "#A6E3A1",
            "Lavender": "#CBA6F7",
        }
        for color_name in self._screensaver_colors:
            self.screensaver_color.addItem(color_name, self._screensaver_colors[color_name])
        saved_color = self.settings.get("screensaver_clock_color", "#F5F5F7")
        color_index = self.screensaver_color.findData(saved_color)
        self.screensaver_color.setCurrentIndex(color_index if color_index >= 0 else 0)
        self.screensaver_color.currentIndexChanged.connect(self.save_screensaver_options)
        screensaver_options.addRow("Clock color", self.screensaver_color)

        self.screensaver_size = QSpinBox()
        self.screensaver_size.setRange(64, 160)
        self.screensaver_size.setSingleStep(8)
        self.screensaver_size.setSuffix(" px")
        try:
            saved_size = int(self.settings.get("screensaver_clock_size", 96))
        except (TypeError, ValueError):
            saved_size = 96
        self.screensaver_size.setValue(max(64, min(160, saved_size)))
        self.screensaver_size.valueChanged.connect(self.save_screensaver_options)
        screensaver_options.addRow("Clock size", self.screensaver_size)

        self.screensaver_time_format = QComboBox()
        self.screensaver_time_format.addItem("24-hour (18:45)", "24h")
        self.screensaver_time_format.addItem("12-hour (06:45 PM)", "12h")
        format_index = self.screensaver_time_format.findData(self.settings.get("screensaver_time_format", "24h"))
        self.screensaver_time_format.setCurrentIndex(format_index if format_index >= 0 else 0)
        self.screensaver_time_format.currentIndexChanged.connect(self.save_screensaver_options)
        screensaver_options.addRow("Time format", self.screensaver_time_format)
        layout.addLayout(screensaver_options)

        # Persist the chosen screensaver configuration alongside existing settings.
        self.settings.setdefault("screensaver_mode", "clock")
        self.settings.setdefault("screensaver_background", "black")
        try:
            save_settings(self.settings)
        except OSError:
            pass

        self.status = QLabel("Ready")
        self.status.setObjectName("status")
        layout.addWidget(self.status)

        self.setStyleSheet("""
            QMainWindow, QWidget#central { background-color: #17181D; }
            QLabel { color: #F3F3F8; font-family: "Segoe UI"; }
            QLabel#title { font-size: 30px; font-weight: 700; }
            QLabel#subtitle { color: #AAABB8; font-size: 13px; }
            QLabel#section { font-size: 18px; font-weight: 600; margin-top: 8px; }
            QLabel#preview {
                background-color: #22232B; border: 1px solid #343540;
                border-radius: 12px; color: #AAABB8; padding: 8px;
            }
            QLabel#status { color: #AAABB8; padding-top: 8px; }
            QPushButton {
                background-color: #292A34; color: #F3F3F8;
                border: 1px solid #41424F; border-radius: 8px;
                padding: 11px 16px; font-size: 13px;
            }
            QPushButton:hover { background-color: #383946; }
            QPushButton#primary { background-color: #6869D9; border: none; font-weight: 600; }
            QPushButton#primary:hover { background-color: #7B7CEB; }
            QPushButton:disabled { color: #777886; background-color: #22232B; }
            QComboBox, QSpinBox {
                background-color: #22232B; color: #F3F3F8;
                border: 1px solid #41424F; border-radius: 6px; padding: 7px;
            }
        """)

        saved_path = self.settings.get("wallpaper_path")
        if saved_path and Path(saved_path).is_file():
            self.image_path = saved_path
            self.path_label.setText(saved_path)
            self.apply_button.setEnabled(True)
            pixmap = QPixmap(saved_path)
            self._set_preview(pixmap)
            self.status.setText("Previous wallpaper loaded.")
        elif saved_path:
            self.status.setText("Previous wallpaper file not found. Choose another image.")

        self._setup_tray()

    def _setup_tray(self):
        self.tray = QSystemTrayIcon(self)
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray.setIcon(icon)
        self.setWindowIcon(icon)
        self.tray.setToolTip("AuraDesktop")

        self.tray_menu = QMenu(self)
        self.show_action = self.tray_menu.addAction("Show AuraDesktop")
        self.show_action.triggered.connect(self.show_main_window)
        self.clock_action = self.tray_menu.addAction("Show Clock")
        self.clock_action.triggered.connect(self.toggle_clock)
        self.tray_menu.addSeparator()
        self.exit_action = self.tray_menu.addAction("Exit")
        self.exit_action.triggered.connect(self.exit_application)

        self.tray.setContextMenu(self.tray_menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

    def _set_preview(self, pixmap):
        if pixmap.isNull():
            self.preview.setText("Unable to preview this image")
            self.preview.setPixmap(QPixmap())
            return
        self.preview.setPixmap(pixmap.scaled(
            self.preview.size(), Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))

    def choose_image(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Choose Wallpaper", str(Path.home() / "Pictures"),
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if not filename:
            return
        pixmap = QPixmap(filename)
        if pixmap.isNull():
            QMessageBox.warning(self, "Invalid Image", "The selected image could not be loaded.")
            return

        self.image_path = filename
        self.path_label.setText(filename)
        self.settings["wallpaper_path"] = filename
        try:
            save_settings(self.settings)
        except OSError as exc:
            self.status.setText(f"Could not save settings: {exc}")
        self._set_preview(pixmap)
        self.apply_button.setEnabled(True)
        self.status.setText("Image loaded successfully.")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.image_path:
            self._set_preview(QPixmap(self.image_path))

    def apply_wallpaper(self):
        if not self.image_path:
            return
        try:
            result = ctypes.windll.user32.SystemParametersInfoW(
                20, 0, self.image_path, 0x01 | 0x02
            )
            if result:
                self.status.setText("Wallpaper applied successfully.")
                QMessageBox.information(self, "Wallpaper Updated", "Your desktop wallpaper has been changed.")
            else:
                error_code = ctypes.get_last_error()
                QMessageBox.warning(self, "Failed", f"Windows could not set the wallpaper. Error: {error_code}")
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def save_screensaver_options(self, *_):
        self.settings["screensaver_mode"] = "clock"
        self.settings["screensaver_background"] = "black"
        self.settings["screensaver_clock_color"] = self.screensaver_color.currentData()
        self.settings["screensaver_clock_size"] = self.screensaver_size.value()
        self.settings["screensaver_time_format"] = self.screensaver_time_format.currentData()
        try:
            save_settings(self.settings)
            if hasattr(self, "_screensaver"):
                self._screensaver.settings = self.settings
                self._screensaver.apply_clock_style()
                self._screensaver.update_clock()
            self.status.setText("Screensaver settings saved.")
        except OSError as exc:
            self.status.setText(f"Could not save screensaver settings: {exc}")

    def preview_screensaver(self):
        # This mode is intentionally a manual preview; idle activation is not enabled.
        self.save_screensaver_options()

        if not hasattr(self, "_screensaver"):
            self._screensaver = ClockScreensaver(self.settings)
            self._screensaver.finished.connect(self._on_screensaver_finished)

        self.hide()
        self._screensaver.show_preview()
        self.status.setText("Clock screensaver preview is running.")

    def _on_screensaver_finished(self):
        self.show_main_window()
        self.status.setText("Screensaver preview closed.")

    def toggle_clock(self):
        if self.clock is None:
            self.clock = DesktopClock(self.settings.get("clock_position"))

        if self.clock.isVisible():
            pos = self.clock.pos()
            self.settings["clock_position"] = [pos.x(), pos.y()]
            try:
                save_settings(self.settings)
            except OSError as exc:
                self.status.setText(f"Could not save clock position: {exc}")
            self.clock.hide()
            self.clock_button.setText("Show Desktop Clock")
            self.clock_action.setText("Show Clock")
            self.status.setText("Desktop Clock hidden.")
            return

        self.clock.show()
        attached = self.clock.attach_to_desktop()
        self.clock_button.setText("Hide Desktop Clock")
        self.clock_action.setText("Hide Clock")
        if attached:
            self.status.setText("Desktop Clock is running on the desktop layer.")
        else:
            self.status.setText("Desktop Clock is running. Desktop attachment could not be confirmed.")

    def show_main_window(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_main_window()

    def exit_application(self):
        self._exiting = True
        if self.clock is not None:
            pos = self.clock.pos()
            self.settings["clock_position"] = [pos.x(), pos.y()]
            try:
                save_settings(self.settings)
            except OSError:
                pass
            self.clock.close()
        self.tray.hide()
        QApplication.quit()

    def closeEvent(self, event):
        if self._exiting:
            event.accept()
            return
        event.ignore()
        self.hide()
        if self.tray.isVisible():
            self.tray.showMessage(
                "AuraDesktop", "AuraDesktop is still running in the system tray.",
                QSystemTrayIcon.MessageIcon.Information, 2000
            )


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("AuraDesktop")
    app.setOrganizationName("AuraDesktop")
    app.setQuitOnLastWindowClosed(False)

    window = AuraDesktop()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

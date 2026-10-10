from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QCursor
from PySide6.QtWidgets import QApplication, QWidget, QLabel
from .core.config import SettingsStore
from .core.saver_args import parse_saver_args
from .core.image_sources import discover_screensaver_images


class ScreenSaver(QWidget):
    def __init__(self, mode, folder):
        super().__init__()
        self.mode = mode
        self.folder = Path(folder) if folder and '\n' not in folder else None
        self.images = discover_screensaver_images(folder)
        self.index = 0
        self.setStyleSheet('background:black;color:white;')
        self.label = QLabel('', self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet('color:white;font-size:44pt;font-weight:600;')
        self.label.setGeometry(self.rect())
        self._last_mouse = QCursor.pos()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)
        self.tick()

    def resizeEvent(self, event):
        self.label.setGeometry(self.rect())

    def tick(self):
        if self.mode == 'Blank':
            self.label.clear()
        elif self.mode == 'Slideshow' and self.images:
            pixmap = QPixmap(str(self.images[self.index % len(self.images)]))
            self.index += 1
            self.label.setPixmap(pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        elif self.mode == 'Slideshow':
            self.label.setText('No slideshow images found')
        else:
            self.label.setText(datetime.now().strftime('%I:%M:%S %p'))

    def keyPressEvent(self, event):
        QApplication.quit()

    def mousePressEvent(self, event):
        QApplication.quit()

    def mouseMoveEvent(self, event):
        # Ignore tiny cursor jitter; a deliberate move exits like a Windows saver.
        current = event.globalPosition().toPoint()
        if abs(current.x() - self._last_mouse.x()) + abs(current.y() - self._last_mouse.y()) >= 12:
            QApplication.quit()
        super().mouseMoveEvent(event)


def _launch_configuration() -> int:
    """Open the app directly on Screensaver settings for Windows /c requests."""
    try:
        if getattr(sys, 'frozen', False):
            app_exe = Path(sys.executable).resolve().with_name('AuraDesktop.exe')
            if not app_exe.is_file():
                return 1
            subprocess.Popen([str(app_exe), '--page', 'Screensaver'], close_fds=True)
        else:
            project_root = Path(__file__).resolve().parents[2]
            entry = project_root / 'main.py'
            subprocess.Popen([sys.executable, str(entry), '--page', 'Screensaver'], close_fds=True)
        return 0
    except (OSError, ValueError):
        return 1


def main():
    command = parse_saver_args(sys.argv[1:])
    if command.mode == 'configure':
        return _launch_configuration()

    app = QApplication(sys.argv)
    app.setApplicationName('AuraDesktop Screensaver')
    settings = SettingsStore()
    folder = settings.get('screensaver_folder', '') if settings.get('screensaver_source', 'Wallpaper Favorites') == 'Separate folder' else '\n'.join(settings.get('wallpaper_favorites', []))
    if command.mode == 'preview':
        saver = ScreenSaver(settings.get('screensaver_mode', 'Clock'), folder)
        if os.name != 'nt' or command.parent_handle is None:
            return 1
        try:
            import ctypes
            import ctypes.wintypes
            user32 = ctypes.windll.user32
            parent = ctypes.wintypes.HWND(command.parent_handle)
            rect = ctypes.wintypes.RECT()
            if not user32.GetClientRect(parent, ctypes.byref(rect)):
                return 1
            saver.show()
            hwnd = ctypes.wintypes.HWND(int(saver.winId()))
            get_style = getattr(user32, 'GetWindowLongPtrW', user32.GetWindowLongW)
            set_style = getattr(user32, 'SetWindowLongPtrW', user32.SetWindowLongW)
            style = get_style(hwnd, -16)
            set_style(hwnd, -16, (style & ~0x80000000) | 0x40000000)
            user32.SetParent(hwnd, parent)
            user32.SetWindowPos(hwnd, 0, 0, 0, rect.right - rect.left, rect.bottom - rect.top, 0x0040)
        except Exception:
            return 1
    else:
        # Create one fullscreen surface per attached display. Keep references alive
        # until the event loop exits; input on any surface quits the saver.
        saver_windows = []
        screens = app.screens() or [app.primaryScreen()]
        for screen in screens:
            if screen is None:
                continue
            window = ScreenSaver(settings.get('screensaver_mode', 'Clock'), folder)
            window.setGeometry(screen.geometry())
            window.showFullScreen()
            saver_windows.append(window)
        if not saver_windows:
            saver = ScreenSaver(settings.get('screensaver_mode', 'Clock'), folder)
            saver.showFullScreen()
    return app.exec()

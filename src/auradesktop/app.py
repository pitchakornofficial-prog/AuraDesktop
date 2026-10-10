from __future__ import annotations
import sys, os, subprocess, shutil, ctypes, time, socket, platform
from pathlib import Path
from datetime import datetime
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QAction, QIcon, QPixmap, QFont
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QFrame, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout, QStackedWidget, QFileDialog, QMessageBox, QComboBox, QCheckBox, QSpinBox, QProgressBar, QSystemTrayIcon, QMenu, QScrollArea, QSlider)
from .core.config import SettingsStore
from .core.theme import LIGHT_STYLESHEET
from .core.telemetry import format_rate, network_rates, bounded_percent, parse_gpu_output
from .core.favorites import add_favorite_path, remove_favorite_path, favorite_display_name
from .core.startup import set_windows_startup
from .core.tray_policy import tray_should_be_visible, close_should_hide_to_tray
try:
    import psutil
except ImportError:
    psutil = None

PAGES = [("Dashboard", "⌂"), ("Wallpaper", "▧"), ("Clock", "◷"), ("Screensaver", "▣"), ("Monitor", "▥"), ("Settings", "⚙")]
class AuraWindow(QMainWindow):
    def __init__(self, initial_page="Dashboard"):
        super().__init__(); self.settings = SettingsStore(); self.setWindowTitle("AuraDesktop"); self.resize(1180, 780); self.setMinimumSize(960, 640); self._allow_exit=False; self._toast_timer=QTimer(self); self._toast_timer.setSingleShot(True)
        central=QWidget(); root=QHBoxLayout(central); root.setContentsMargins(0,0,0,0); root.setSpacing(0); self.setCentralWidget(central)
        sidebar=QFrame(); sidebar.setObjectName('Sidebar'); sidebar.setFixedWidth(218); sl=QVBoxLayout(sidebar); sl.setContentsMargins(16,22,16,16); sl.setSpacing(8)
        brand=QLabel('◈  AuraDesktop'); brand.setStyleSheet('font-size: 17pt; font-weight: 700; padding: 4px 4px 20px 4px;'); sl.addWidget(brand)
        self.nav_buttons=[]
        for i,(name,icon) in enumerate(PAGES):
            b=QPushButton(f'{icon}   {name}'); b.setObjectName('Nav'); b.setCheckable(True); b.clicked.connect(lambda checked=False, n=name:self.show_page(n)); sl.addWidget(b); self.nav_buttons.append(b)
        sl.addStretch(); foot=QLabel('PERSONAL DESKTOP HUB\nWindows 11'); foot.setObjectName('Muted'); sl.addWidget(foot)
        right=QWidget(); rl=QVBoxLayout(right); rl.setContentsMargins(26,22,26,20); rl.setSpacing(16); self.toast=QLabel(''); self.toast.setStyleSheet('background:#e8f7ee;color:#166534;border-radius:8px;padding:9px;'); self.toast.hide(); self._toast_timer.timeout.connect(self.toast.hide); rl.addWidget(self.toast)
        self.stack=QStackedWidget(); rl.addWidget(self.stack,1); root.addWidget(sidebar); root.addWidget(right,1)
        self.pages={}; self._build_dashboard(); self._build_wallpaper(); self._build_clock(); self._build_screensaver(); self._build_monitor(); self._build_settings()
        self._monitor_timer=QTimer(self); self._monitor_timer.timeout.connect(self.refresh_monitor); self._monitor_timer.start(max(1000, int(self.settings.get('monitor_refresh', 2))*1000)); self._clock_timer=QTimer(self); self._clock_timer.timeout.connect(self.update_clock_preview); self._clock_timer.start(1000)
        self._setup_tray(); self.show_page(initial_page if initial_page in self.pages else 'Dashboard'); self.refresh_monitor(); QTimer.singleShot(700, self.restore_clock)
    def card(self,title,subtitle=None):
        f=QFrame(); f.setObjectName('Card'); l=QVBoxLayout(f); l.setContentsMargins(18,16,18,16); l.setSpacing(10); t=QLabel(title); t.setStyleSheet('font-size:12pt;font-weight:650;'); l.addWidget(t)
        if subtitle: s=QLabel(subtitle); s.setObjectName('Muted'); s.setWordWrap(True); l.addWidget(s)
        return f,l
    def page_shell(self,name,desc):
        w=QWidget(); v=QVBoxLayout(w); v.setContentsMargins(0,0,0,0); v.setSpacing(16); title=QLabel(name); title.setObjectName('PageTitle'); v.addWidget(title); d=QLabel(desc); d.setObjectName('Muted'); d.setWordWrap(True); v.addWidget(d); self.stack.addWidget(w); self.pages[name]=(w,v); return w,v
    def add_row(self,layout,label,widget):
        row=QHBoxLayout(); text=QLabel(label); text.setMinimumWidth(180); row.addWidget(text); row.addWidget(widget,1); layout.addLayout(row)
    def confirm(self,title,message): return QMessageBox.question(self,title,message,QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)==QMessageBox.StandardButton.Yes
    def notify(self,message,success=True):
        self.toast.setText(('✓  ' if success else '⚠  ')+message); self.toast.setStyleSheet(('background:#e8f7ee;color:#166534;' if success else 'background:#fff1f0;color:#9f241d;')+'border-radius:8px;padding:9px;'); self.toast.show(); self._toast_timer.start(4000)
    def show_page(self,name):
        idx=next(i for i,(n,_) in enumerate(PAGES) if n==name); self.stack.setCurrentIndex(idx);
        for i,b in enumerate(self.nav_buttons): b.setChecked(i==idx)
    def _build_dashboard(self):
        w,v=self.page_shell('Dashboard','Your desktop, organized in one calm workspace.'); row=QHBoxLayout(); v.addLayout(row)
        for title,desc in [('Wallpaper','Choose a local image and keep favorites.'),('Desktop Clock','Pin a clock to the desktop layer.'),('Screensaver','Clock, slideshow or blank screen.'),('System Monitor','Live readings every 2 seconds.')]:
            f,l=self.card(title,desc); btn=QPushButton('Open'); btn.setObjectName('Primary'); btn.clicked.connect(lambda checked=False,t=title:self.show_page({'Desktop Clock':'Clock','System Monitor':'Monitor'}.get(t,t))); l.addWidget(btn); row.addWidget(f)
        f,l=self.card('Quick status','Current system and feature status'); v.addWidget(f); self.dashboard_status=QLabel('Loading system status…'); self.dashboard_status.setWordWrap(True); l.addWidget(self.dashboard_status); v.addStretch()
    def _build_wallpaper(self):
        w,v=self.page_shell('Wallpaper','Select a local image, preview it, and apply it across your displays.'); f,l=self.card('Wallpaper library','The same image is applied to all monitors using Windows desktop wallpaper settings.'); v.addWidget(f)
        self.wall_path=QLabel(self.settings.get('wallpaper_path') or 'No image selected'); self.wall_path.setWordWrap(True); l.addWidget(self.wall_path)
        row=QHBoxLayout(); choose=QPushButton('Choose image…'); choose.clicked.connect(self.choose_wallpaper); row.addWidget(choose); apply=QPushButton('Apply wallpaper'); apply.setObjectName('Primary'); apply.clicked.connect(self.apply_wallpaper); row.addWidget(apply); l.addLayout(row)
        self.wall_preview=QLabel('Image preview'); self.wall_preview.setAlignment(Qt.AlignmentFlag.AlignCenter); self.wall_preview.setMinimumHeight(240); self.wall_preview.setStyleSheet('background:#eef2f7;border-radius:10px;color:#68778c;'); l.addWidget(self.wall_preview)
        self.wall_fit=QComboBox(); self.wall_fit.addItems(['Fill','Fit','Stretch','Center']); self.wall_fit.setCurrentText(self.settings.get('wallpaper_fit','Fill')); self.add_row(l,'Fit mode',self.wall_fit)
        favrow=QHBoxLayout(); fav=QPushButton('Add current image to Favorites'); fav.clicked.connect(self.add_favorite); favrow.addWidget(fav); self.fav_combo=QComboBox(); self.refresh_favorites(); favrow.addWidget(self.fav_combo,1); usefav=QPushButton('Use favorite'); usefav.clicked.connect(self.use_favorite); favrow.addWidget(usefav); removefav=QPushButton('Remove'); removefav.clicked.connect(self.remove_favorite); favrow.addWidget(removefav); l.addLayout(favrow); v.addStretch()
        if self.settings.get('wallpaper_path'): self.set_wallpaper_preview(self.settings.get('wallpaper_path'))
    def choose_wallpaper(self):
        path,_=QFileDialog.getOpenFileName(self,'Choose wallpaper','','Images (*.png *.jpg *.jpeg *.bmp *.webp)')
        if path:
            if QPixmap(path).isNull(): self.notify('This image could not be opened.',False); return
            if not self.confirm('Choose wallpaper',f'Use this image?\n{path}'): return
            self.settings.set('wallpaper_path',path); self.wall_path.setText(path); self.set_wallpaper_preview(path); self.notify('Wallpaper selection saved.')
    def set_wallpaper_preview(self,path):
        pix=QPixmap(path)
        if pix.isNull(): self.wall_preview.setText('Preview unavailable'); return
        self.wall_preview.setPixmap(pix.scaled(QSize(700,300),Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
    def apply_wallpaper(self):
        path=self.settings.get('wallpaper_path','')
        if not path or not Path(path).is_file(): self.notify('Choose a valid image first.',False); return
        if not self.confirm('Apply wallpaper','Apply this image as the Windows desktop wallpaper on all monitors?'): return
        if os.name!='nt': self.notify('Applying wallpaper requires Windows 11.',False); return
        try:
            SPI_SETDESKWALLPAPER=20; SPIF_UPDATEINIFILE=1; SPIF_SENDCHANGE=2
            style={'Fill':10,'Fit':6,'Stretch':2,'Center':0}.get(self.wall_fit.currentText(),10)
            import winreg
            key=winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Control Panel\Desktop',0,winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key,'WallpaperStyle',0,winreg.REG_SZ,str(style)); winreg.SetValueEx(key,'TileWallpaper',0,winreg.REG_SZ,'0'); winreg.CloseKey(key)
            ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER,0,path,SPIF_UPDATEINIFILE|SPIF_SENDCHANGE)
            self.settings.set('wallpaper_fit',self.wall_fit.currentText()); self.notify('Windows wallpaper applied.')
        except Exception as e: self.notify(f'Could not apply wallpaper: {e}',False)
    def refresh_favorites(self):
        if not hasattr(self,'fav_combo'): return
        self.fav_combo.clear()
        for p in self.settings.get('wallpaper_favorites',[]): self.fav_combo.addItem(favorite_display_name(p),p)
    def add_favorite(self):
        path=self.settings.get('wallpaper_path','')
        if not path or not Path(path).is_file(): self.notify('Choose a valid image first.',False); return
        favs, added = add_favorite_path(self.settings.get('wallpaper_favorites', []), path)
        if not added: self.notify('Image is already in Favorites.',False); return
        if self.confirm('Add to Favorites','Save this image to Wallpaper Favorites?'):
            self.settings.set('wallpaper_favorites',favs); self.refresh_favorites(); self.notify('Added to Favorites.')
    def remove_favorite(self):
        path=self.fav_combo.currentData()
        if not path:
            self.notify('Select a favorite to remove.',False); return
        if not self.confirm('Remove favorite',f'Remove this image from Wallpaper Favorites?\n{path}'):
            return
        favorites=remove_favorite_path(self.settings.get('wallpaper_favorites', []), path)
        self.settings.set('wallpaper_favorites', favorites)
        self.refresh_favorites()
        self.notify('Removed from Favorites. The image file was not deleted.')
    def use_favorite(self):
        path=self.fav_combo.currentData()
        if not path or not Path(path).is_file():
            self.notify('Favorite file is missing.',False)
            return
        if not self.confirm('Use wallpaper favorite', f'Select this image as the current wallpaper?\n{path}'):
            return
        self.settings.set('wallpaper_path',path)
        self.wall_path.setText(path)
        self.set_wallpaper_preview(path)
        self.notify('Favorite selected. Use Apply wallpaper to update Windows.')
    def _build_clock(self):
        w,v=self.page_shell('Desktop Clock','Experimental Windows desktop-layer clock. Shell behavior varies by Windows build.'); f,l=self.card('Clock appearance','The clock is intended to live on the desktop layer, behind ordinary app windows.'); v.addWidget(f)
        self.clock_preview=QLabel('10:08:42'); self.clock_preview.setAlignment(Qt.AlignmentFlag.AlignCenter); self.clock_preview.setStyleSheet('font-size:34pt;font-weight:700;background:#edf3ff;border-radius:12px;padding:24px;color:#1d4ed8;'); l.addWidget(self.clock_preview)
        self.clock_position=QComboBox(); self.clock_position.addItems(['Top Left','Top Right','Bottom Left','Bottom Right','Center']); self.clock_position.setCurrentText(self.settings.get('clock_position','Top Right')); self.add_row(l,'Position preset',self.clock_position)
        self.clock_size=QComboBox(); self.clock_size.addItems(['Small','Medium','Large']); self.clock_size.setCurrentText(self.settings.get('clock_size','Medium')); self.add_row(l,'Size',self.clock_size)
        self.clock_monitor=QComboBox(); self.clock_monitor.addItems([f'Display {i+1}' for i in range(max(1,len(QApplication.screens())))]); self.clock_monitor.setCurrentIndex(min(self.settings.get('clock_monitor',0),self.clock_monitor.count()-1)); self.add_row(l,'Monitor',self.clock_monitor)
        row=QHBoxLayout(); start=QPushButton('Enable desktop clock'); start.setObjectName('Primary'); start.clicked.connect(self.enable_clock); row.addWidget(start); stop=QPushButton('Disable clock'); stop.clicked.connect(self.disable_clock); row.addWidget(stop); l.addLayout(row); note=QLabel('Note: WorkerW integration is Windows-shell dependent. Confirm this behavior on the target PC before relying on it.'); note.setObjectName('Muted'); note.setWordWrap(True); l.addWidget(note); v.addStretch()
    def update_clock_preview(self):
        if hasattr(self,'clock_preview'): self.clock_preview.setText(datetime.now().strftime('%I:%M:%S %p'))
        if hasattr(self,'desktop_clock') and self.desktop_clock and self.desktop_clock.isVisible(): self.desktop_clock.setText(datetime.now().strftime('%I:%M:%S %p'))
    def enable_clock(self):
        if not self.confirm('Enable desktop clock','Attempt to place the clock on the Windows desktop layer? This is experimental and may vary by Windows build.'): return
        if os.name!='nt':
            self.notify('Desktop-layer clock requires Windows; no clock state was changed.',False)
            return
        try:
            self.settings.set('clock_position',self.clock_position.currentText())
            self.settings.set('clock_size',self.clock_size.currentText())
            self.settings.set('clock_monitor',self.clock_monitor.currentIndex())
            if hasattr(self,'desktop_clock') and self.desktop_clock: self.desktop_clock.close()
            self.settings.set('clock_x', None); self.settings.set('clock_y', None)
            self.desktop_clock=DesktopClock(self.clock_position.currentText(),self.clock_size.currentText(),self.clock_monitor.currentIndex(), on_position_saved=self.save_clock_position); self.desktop_clock.show(); self.settings.set('clock_position',self.clock_position.currentText()); self.settings.set('clock_size',self.clock_size.currentText()); self.settings.set('clock_monitor',self.clock_monitor.currentIndex()); self.settings.set('clock_enabled',True); self.notify('Clock launched; verify it stays behind app windows.')
        except Exception as e: self.notify(f'Could not launch desktop clock: {e}',False)
    def restore_clock(self):
        if self.settings.get('clock_enabled', False) and os.name == 'nt':
            try:
                self.desktop_clock=DesktopClock(self.settings.get('clock_position','Top Right'),self.settings.get('clock_size','Medium'),self.settings.get('clock_monitor',0), initial_xy=(self.settings.get('clock_x'), self.settings.get('clock_y')), on_position_saved=self.save_clock_position); self.desktop_clock.show()
            except Exception as e: self.notify(f'Could not restore desktop clock: {e}',False)
    def disable_clock(self):
        if not self.confirm('Disable clock','Turn off the desktop clock?'): return
        if hasattr(self,'desktop_clock') and self.desktop_clock: self.desktop_clock.close()
        self.settings.set('clock_enabled',False); self.notify('Desktop clock disabled.')
    def save_clock_position(self, x, y, monitor):
        try:
            self.settings.set('clock_x', int(x))
            self.settings.set('clock_y', int(y))
            self.settings.set('clock_monitor', int(monitor))
        except (OSError, TypeError, ValueError) as exc:
            self.notify(f'Clock moved, but its position could not be saved: {exc}', False)
    def _build_screensaver(self):
        w,v=self.page_shell('Screensaver','Configure the saver mode and Windows idle timeout.'); f,l=self.card('Screensaver options','The installed AuraDesktop.scr can be registered with Windows Screen Saver Settings.'); v.addWidget(f)
        self.ss_mode=QComboBox(); self.ss_mode.addItems(['Clock','Slideshow','Blank']); self.ss_mode.setCurrentText(self.settings.get('screensaver_mode','Clock')); self.add_row(l,'Mode',self.ss_mode)
        self.ss_source=QComboBox(); self.ss_source.addItems(['Wallpaper Favorites','Separate folder']); self.ss_source.setCurrentText(self.settings.get('screensaver_source','Wallpaper Favorites')); self.add_row(l,'Slideshow source',self.ss_source)
        self.ss_folder=QLabel(self.settings.get('screensaver_folder') or 'No slideshow folder selected'); self.ss_folder.setWordWrap(True); folder=QPushButton('Choose slideshow folder…'); folder.clicked.connect(self.choose_ss_folder); l.addWidget(self.ss_folder); l.addWidget(folder)
        self.ss_timeout=QSpinBox(); self.ss_timeout.setRange(1,120); self.ss_timeout.setSuffix(' minutes'); self.ss_timeout.setValue(self.settings.get('screensaver_timeout',10)); self.add_row(l,'Windows idle timeout',self.ss_timeout)
        row=QHBoxLayout(); save=QPushButton('Save screensaver settings'); save.setObjectName('Primary'); save.clicked.connect(self.save_screensaver); row.addWidget(save); preview=QPushButton('Preview'); preview.clicked.connect(self.preview_screensaver); row.addWidget(preview); l.addLayout(row)
        note=QLabel('Saving registers AuraDesktop.scr when the built file is found. Windows Screen Saver Settings remains the place to verify activation and preview behavior.'); note.setObjectName('Muted'); note.setWordWrap(True); l.addWidget(note); v.addStretch()
    def choose_ss_folder(self):
        p=QFileDialog.getExistingDirectory(self,'Choose slideshow folder')
        if p and self.confirm('Slideshow folder',f'Use this folder for screensaver images?\n{p}'):
            self.settings.set('screensaver_folder',p); self.ss_folder.setText(p); self.notify('Slideshow folder saved.')
    def save_screensaver(self):
        if not self.confirm('Save screensaver','Save the selected mode and timeout?'): return
        self.settings.set('screensaver_mode',self.ss_mode.currentText()); self.settings.set('screensaver_source',self.ss_source.currentText()); self.settings.set('screensaver_timeout',self.ss_timeout.value())
        try:
            if os.name == 'nt':
                import winreg
                key=winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Control Panel\Desktop',0,winreg.KEY_SET_VALUE)
                try:
                    winreg.SetValueEx(key,'ScreenSaveTimeOut',0,winreg.REG_SZ,str(self.ss_timeout.value()*60))
                    winreg.SetValueEx(key,'ScreenSaveActive',0,winreg.REG_SZ,'1')
                finally:
                    winreg.CloseKey(key)
                saver_path=self.find_screensaver_path()
                if saver_path:
                    key=winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Control Panel\Desktop',0,winreg.KEY_SET_VALUE)
                    try: winreg.SetValueEx(key,'SCRNSAVE.EXE',0,winreg.REG_SZ,str(saver_path))
                    finally: winreg.CloseKey(key)
                else:
                    self.notify('Preferences saved, but AuraDesktop.scr was not found. Build/install the screensaver to register it with Windows.',False); return
            self.notify('Screensaver preferences saved and Windows registration updated.')
        except Exception as e: self.notify(f'Preferences saved locally, but Windows integration failed: {e}',False)
    def find_screensaver_path(self):
        candidates=[]
        if getattr(sys,'frozen',False):
            candidates.append(Path(sys.executable).resolve().with_name('AuraDesktop.scr'))
        project_root=Path(__file__).resolve().parents[2]
        candidates.extend([project_root/'dist'/'AuraDesktop'/'AuraDesktop.scr', project_root/'AuraDesktop.scr'])
        return next((p for p in candidates if p.is_file()),None)
    def preview_screensaver(self):
        if not self.confirm('Preview screensaver','Open a preview window? Press any key or click to close.'): return
        folder=self.settings.get('screensaver_folder','') if self.settings.get('screensaver_source','Wallpaper Favorites')=='Separate folder' else '\n'.join(self.settings.get('wallpaper_favorites',[]))
        self.saver_preview=SaverPreview(self.settings.get('screensaver_mode','Clock'),folder); self.saver_preview.showFullScreen()
    def _build_monitor(self):
        w,v=self.page_shell('System Monitor','Live metrics refresh every 2 seconds. Unsupported telemetry is shown as unavailable.'); grid=QGridLayout(); v.addLayout(grid); self.metric_labels={}; self.metric_bars={}
        for i,(key,title) in enumerate([('cpu','CPU utilization'),('ram','Memory utilization'),('disk','Disk utilization'),('net','Network RX / TX'),('gpu','GPU utilization / temperature'),('battery','Battery')]):
            f,l=self.card(title); value=QLabel('—'); value.setStyleSheet('font-size:19pt;font-weight:650;'); l.addWidget(value); bar=QProgressBar(); bar.setRange(0,100); bar.setValue(0); l.addWidget(bar); grid.addWidget(f,i//2,i%2); self.metric_labels[key]=value; self.metric_bars[key]=bar
        self.monitor_note=QLabel('Metrics are sourced from the OS and installed drivers; unavailable sensors are never replaced with estimates.'); self.monitor_note.setObjectName('Muted'); v.addWidget(self.monitor_note); v.addStretch()
    def refresh_monitor(self):
        if psutil is None:
            for key in getattr(self, 'metric_labels', {}):
                self.metric_labels[key].setText('Unavailable (psutil not installed)')
                self.metric_bars[key].setValue(0)
            if hasattr(self, 'monitor_note'):
                self.monitor_note.setText('System metrics unavailable because psutil is not installed.')
            return
        try:
            cpu=psutil.cpu_percent(interval=None); mem=psutil.virtual_memory(); disk=psutil.disk_usage(os.getenv('SystemDrive','C:')+'\\' if os.name=='nt' else '/'); net=psutil.net_io_counters(); now=time.monotonic()
            rx,tx,self._net_prev=network_rates(net.bytes_recv,net.bytes_sent,now,getattr(self,'_net_prev',None))
            vals={'cpu':(f'{cpu:.0f}%',cpu),'ram':(f'{mem.percent:.0f}% · {mem.used/1024**3:.1f}/{mem.total/1024**3:.1f} GB',mem.percent),'disk':(f'{disk.percent:.0f}% used',disk.percent),'net':(f'↓ {self.fmt_rate(rx)}   ↑ {self.fmt_rate(tx)}',0)}
            try:
                batt=psutil.sensors_battery(); vals['battery']=(f'{batt.percent:.0f}%'+(' · charging' if batt.power_plugged else '') if batt else 'Unavailable on this device',batt.percent if batt else 0)
            except Exception: vals['battery']=('Unavailable',0)
            vals['gpu']=self.gpu_metrics()
            for k,(text,pct) in vals.items():
                self.metric_labels[k].setText(text); self.metric_bars[k].setValue(bounded_percent(pct))
                if k in ('net','gpu') and (text=='Unavailable' or text.startswith('Unavailable')): self.metric_bars[k].setValue(0)
            if hasattr(self,'dashboard_status'): self.dashboard_status.setText(f'OS: {platform.system()} {platform.release()}  ·  CPU: {psutil.cpu_count(logical=True)} logical cores  ·  Memory: {mem.total/1024**3:.1f} GB\nWallpaper: {"Selected" if self.settings.get("wallpaper_path") else "Not configured"}  ·  Clock: {"Enabled" if self.settings.get("clock_enabled") else "Off"}  ·  Screensaver: {self.settings.get("screensaver_mode")}')
        except Exception as e:
            if hasattr(self,'monitor_note'): self.monitor_note.setText(f'System metrics unavailable: {e}')
    def fmt_rate(self,n):
        return format_rate(n)
    def gpu_metrics(self):
        exe=shutil.which('nvidia-smi')
        if exe:
            try:
                result=subprocess.run([exe,'--query-gpu=utilization.gpu,temperature.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=2,check=True)
                return parse_gpu_output(result.stdout)
            except Exception:
                return ('Unavailable (GPU query failed)',0)
        return ('Unavailable (no supported GPU telemetry)',0)
    def _build_settings(self):
        w,v=self.page_shell('Settings','Behavior and Windows integration. Changes are saved locally and require confirmation.'); f,l=self.card('App behavior','Closing the window can hide the app to the system tray. Use Exit in the tray menu to stop background features.'); v.addWidget(f)
        self.tray_check=QCheckBox('Keep AuraDesktop available in the System Tray'); self.tray_check.setChecked(self.settings.get('minimize_to_tray',True)); l.addWidget(self.tray_check)
        self.close_check=QCheckBox('Hide to tray when the window is closed'); self.close_check.setChecked(self.settings.get('close_to_tray',True)); l.addWidget(self.close_check)
        self.start_check=QCheckBox('Launch AuraDesktop when I sign in to Windows'); self.start_check.setChecked(self.settings.get('launch_on_startup',False)); l.addWidget(self.start_check)
        save=QPushButton('Save settings'); save.setObjectName('Primary'); save.clicked.connect(self.save_settings); l.addWidget(save)
        f2,l2=self.card('Data and compatibility','Settings are stored in your Windows user profile. GPU temperature depends on compatible hardware and drivers.'); v.addWidget(f2); lbl=QLabel('Python requirement: 3.15.0 exactly. This package does not change your Python installation.'); lbl.setWordWrap(True); l2.addWidget(lbl); v.addStretch()
    def save_settings(self):
        if not self.confirm('Save settings','Apply these behavior settings?'): return
        requested=self.start_check.isChecked()
        tray_enabled = self.tray_check.isChecked()
        close_to_tray = self.close_check.isChecked() and tray_enabled
        if self.close_check.isChecked() and not tray_enabled:
            self.notify('Close-to-tray requires the System Tray option. It will be disabled.', False)
        try:
            self.set_startup(requested)
            self.settings.set('minimize_to_tray', tray_enabled)
            self.settings.set('close_to_tray', close_to_tray)
            self.settings.set('launch_on_startup', requested)
            self.close_check.setChecked(close_to_tray)
            self.apply_tray_settings()
            self.notify('Settings saved.')
        except Exception as e:
            self.start_check.setChecked(self.settings.get('launch_on_startup',False))
            self.tray_check.setChecked(self.settings.get('minimize_to_tray',True))
            self.close_check.setChecked(self.settings.get('close_to_tray',True))
            self.notify(f'Could not update Windows startup: {e}',False)
    def set_startup(self,enabled):
        entry = Path(__file__).resolve().parents[2] / 'main.py'
        set_windows_startup(
            enabled,
            executable=sys.executable,
            frozen=bool(getattr(sys, 'frozen', False)),
            entry_script=entry,
        )
    def _setup_tray(self):
        self.tray=QSystemTrayIcon(self)
        self.tray.setToolTip('AuraDesktop')
        self.tray.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))
        menu=QMenu()
        open_action=QAction('Open AuraDesktop',self)
        open_action.triggered.connect(self.show_from_tray)
        menu.addAction(open_action)
        menu.addSeparator()
        exit_action=QAction('Exit AuraDesktop',self)
        exit_action.triggered.connect(self.exit_app)
        menu.addAction(exit_action)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda reason:self.show_from_tray() if reason==QSystemTrayIcon.ActivationReason.Trigger else None)
        self.apply_tray_settings()
    def apply_tray_settings(self):
        # Apply persisted tray visibility without assuming a tray exists on every host.
        if not hasattr(self, 'tray'):
            return
        available = QSystemTrayIcon.isSystemTrayAvailable()
        if tray_should_be_visible(self.settings.data, available):
            self.tray.show()
        else:
            self.tray.hide()
    def show_from_tray(self): self.showNormal(); self.raise_(); self.activateWindow()
    def _stop_background_features(self):
        # Stop timers first so no callbacks run while the app is shutting down.
        for timer_name in ('_monitor_timer', '_clock_timer', '_toast_timer'):
            timer = getattr(self, timer_name, None)
            if timer is not None:
                timer.stop()
        clock = getattr(self, 'desktop_clock', None)
        if clock is not None:
            clock.close()
        tray = getattr(self, 'tray', None)
        if tray is not None:
            tray.hide()
    def exit_app(self):
        if not self.confirm('Exit AuraDesktop','Exit and stop background features?'): return
        self._allow_exit=True
        self._stop_background_features()
        QApplication.quit()
    def closeEvent(self,event):
        tray_available = QSystemTrayIcon.isSystemTrayAvailable()
        if close_should_hide_to_tray(self.settings.data, tray_available, allow_exit=self._allow_exit):
            event.ignore(); self.hide(); self.tray.show(); self.tray.showMessage('AuraDesktop','Still running in the system tray.',QSystemTrayIcon.MessageIcon.Information,2500)
        elif not self._allow_exit:
            if self.confirm('Exit AuraDesktop','Close the app and stop background features?'):
                self._allow_exit=True
                self._stop_background_features()
                event.accept(); QTimer.singleShot(0,QApplication.quit)
            else: event.ignore()
        else:
            self._stop_background_features()
            event.accept()
class DesktopClock(QLabel):
    """Experimental Windows desktop-layer clock with persistent drag position."""
    def __init__(self, position, size, monitor, initial_xy=None, on_position_saved=None):
        super().__init__('')
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnBottomHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet('background:rgba(255,255,255,190);color:#17243b;border-radius:14px;padding:12px;')
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        size = size if size in {'Small','Medium','Large'} else 'Medium'
        self.position = position if position in {'Top Left','Top Right','Bottom Left','Bottom Right','Center'} else 'Top Right'
        self.monitor = max(0, int(monitor))
        self.initial_xy = initial_xy if isinstance(initial_xy, tuple) and len(initial_xy) == 2 and all(isinstance(v, int) and not isinstance(v, bool) for v in initial_xy) else None
        self.on_position_saved = on_position_saved
        self.setFont(QFont('Segoe UI', {'Small':18,'Medium':28,'Large':42}[size], QFont.Weight.DemiBold))
        self.resize({'Small':180,'Medium':280,'Large':380}[size],85)
        self._drag = None

    def showEvent(self, event):
        super().showEvent(event)
        if os.name == 'nt':
            try:
                hwnd = int(self.winId())
                user32 = ctypes.windll.user32
                prog = user32.FindWindowW('Progman', None)
                result = ctypes.c_ulong()
                user32.SendMessageTimeoutW(prog, 0x052C, 0, 0, 0, 1000, ctypes.byref(result))
                workers = []
                EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
                def enum(hwnd, lparam):
                    shell = user32.FindWindowExW(hwnd, 0, 'SHELLDLL_DefView', None)
                    if shell:
                        workers.append(user32.FindWindowExW(0, hwnd, 'WorkerW', None))
                    return True
                user32.EnumWindows(EnumProc(enum), 0)
                parent = next((x for x in workers if x), prog)
                get_style = getattr(user32, 'GetWindowLongPtrW', user32.GetWindowLongW)
                set_style = getattr(user32, 'SetWindowLongPtrW', user32.SetWindowLongW)
                style = get_style(hwnd, -16)
                set_style(hwnd, -16, (style & ~0x80000000) | 0x40000000)
                user32.SetParent(hwnd, parent)
            except Exception:
                # The UI will still show a clock; final Windows testing must
                # verify whether it actually stays on the desktop layer.
                pass
        screens = QApplication.screens()
        if not screens:
            return
        screen = screens[min(self.monitor, len(screens)-1)]
        g = screen.availableGeometry()
        margin = 30
        coords = {
            'Top Left': (g.left()+margin, g.top()+margin),
            'Top Right': (g.right()-self.width()-margin, g.top()+margin),
            'Bottom Left': (g.left()+margin, g.bottom()-self.height()-margin),
            'Bottom Right': (g.right()-self.width()-margin, g.bottom()-self.height()-margin),
            'Center': (g.center().x()-self.width()//2, g.center().y()-self.height()//2),
        }
        self.move(*(self.initial_xy if self.initial_xy is not None else coords[self.position]))

    def mousePressEvent(self, event):
        self._drag = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        event.accept()

    def mouseMoveEvent(self, event):
        if self._drag is not None:
            self.move(event.globalPosition().toPoint() - self._drag)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag = None
        if self.on_position_saved:
            center = self.frameGeometry().center()
            screen = QApplication.screenAt(center)
            screens = QApplication.screens()
            monitor = screens.index(screen) if screen in screens else min(self.monitor, max(0, len(screens)-1))
            self.monitor = monitor
            try:
                self.on_position_saved(self.x(), self.y(), monitor)
            except Exception:
                pass
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

class SaverPreview(QWidget):
    def __init__(self,mode,folder):
        super().__init__(); self.mode=mode; self.folder=folder; self.setWindowFlags(Qt.WindowType.Window|Qt.WindowType.FramelessWindowHint); self.setStyleSheet('background:black;color:white;'); self.label=QLabel('',self); self.label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.label.setStyleSheet('color:white;font-size:42pt;font-weight:600;'); self.label.setGeometry(self.rect()); self.timer=QTimer(self); self.timer.timeout.connect(self.update_frame); self.timer.start(1000); self.update_frame()
    def resizeEvent(self,e): self.label.setGeometry(self.rect())
    def update_frame(self):
        if self.mode=='Clock': self.label.setText(datetime.now().strftime('%H:%M:%S'))
        elif self.mode=='Blank': self.label.setText(' ')
        else:
            paths=[p for p in self.folder.splitlines() if p and Path(p).is_file()]
            if paths:
                self._slide_index=getattr(self,'_slide_index',-1)+1; pix=QPixmap(paths[self._slide_index%len(paths)]); self.label.setPixmap(pix.scaled(self.size(),Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
            else: self.label.setText('No slideshow images found')
    def keyPressEvent(self,e): self.close()
    def mousePressEvent(self,e): self.close()
def main():
    initial_page = 'Dashboard'
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg == '--page' and i + 1 < len(args):
            initial_page = args[i + 1]
        elif arg.startswith('--page='):
            initial_page = arg.split('=', 1)[1]
    app=QApplication(sys.argv); app.setApplicationName('AuraDesktop'); app.setQuitOnLastWindowClosed(False); app.setStyleSheet(LIGHT_STYLESHEET); win=AuraWindow(initial_page); win.show(); return app.exec()

LIGHT_STYLESHEET = r"""
QWidget { background: #f5f7fb; color: #182230; font-family: 'Segoe UI'; font-size: 10pt; }
QMainWindow, QDialog { background: #f5f7fb; }
QFrame#Sidebar { background: #ffffff; border-right: 1px solid #e3e8f0; }
QFrame#Card { background: #ffffff; border: 1px solid #e4e9f1; border-radius: 14px; }
QLabel#PageTitle { font-size: 22pt; font-weight: 650; color: #152238; }
QLabel#Muted { color: #68778c; }
QPushButton { background: #ffffff; border: 1px solid #d6deea; border-radius: 8px; padding: 8px 13px; }
QPushButton:hover { background: #edf3ff; border-color: #a9c3f7; }
QPushButton#Primary { background: #2563eb; color: white; border: 1px solid #2563eb; font-weight: 600; }
QPushButton#Primary:hover { background: #1d4ed8; }
QPushButton#Nav { text-align: left; padding: 11px 13px; border: 0; background: transparent; color: #4c5b70; }
QPushButton#Nav:checked { background: #eaf1ff; color: #1d4ed8; font-weight: 600; }
QLineEdit, QComboBox, QSpinBox { background: #ffffff; border: 1px solid #d6deea; border-radius: 7px; padding: 7px; }
QCheckBox { spacing: 8px; }
QProgressBar { border: 0; border-radius: 4px; background: #e8edf5; height: 8px; text-align: center; }
QProgressBar::chunk { background: #3978ed; border-radius: 4px; }
QTableWidget { background: white; border: 1px solid #e4e9f1; border-radius: 10px; gridline-color: #edf0f5; }
QHeaderView::section { background: #f7f9fc; border: 0; padding: 8px; font-weight: 600; }
"""

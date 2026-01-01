"""
华为平板PDF阅读器 - UI模块

基于Kivy框架的用户界面实现。
"""

from huawei_pdf_reader.ui.theme import Theme, DARK_GREEN_THEME
from huawei_pdf_reader.ui.main_window import MainWindow
from huawei_pdf_reader.ui.file_manager_view import FileManagerView
from huawei_pdf_reader.ui.reader_view import ReaderView
from huawei_pdf_reader.ui.settings_view import SettingsView
from huawei_pdf_reader.ui.annotation_tools import AnnotationToolbar, PenSelector, ColorPicker, WidthSlider
from huawei_pdf_reader.ui.magnifier_widget import MagnifierWidget

__all__ = [
    "Theme",
    "DARK_GREEN_THEME",
    "MainWindow",
    "FileManagerView",
    "ReaderView",
    "SettingsView",
    "AnnotationToolbar",
    "PenSelector",
    "ColorPicker",
    "WidthSlider",
    "MagnifierWidget",
]

"""
华为平板PDF阅读器 - 主窗口

实现主窗口和导航框架。
Requirements: 12.1, 12.6
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.properties import (
    ObjectProperty, StringProperty, BooleanProperty, 
    ListProperty, NumericProperty
)
from kivy.clock import Clock
from kivy.core.window import Window
from pathlib import Path
from typing import Optional, Callable, List, TYPE_CHECKING

from huawei_pdf_reader.ui.theme import Theme, DARK_GREEN_THEME, get_theme
from huawei_pdf_reader.models import Settings

if TYPE_CHECKING:
    from huawei_pdf_reader.app import Application


class NavItem(BoxLayout):
    """导航栏项目"""
    
    text = StringProperty("")
    icon = StringProperty("")
    selected = BooleanProperty(False)
    on_select = ObjectProperty(None)
    
    def __init__(self, text: str = "", icon: str = "", 
                 on_select: Optional[Callable] = None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 50
        self.padding = [15, 5, 15, 5]
        self.spacing = 10
        
        self.text = text
        self.icon = icon
        self.on_select = on_select
        
        self._theme = DARK_GREEN_THEME
        self._setup_ui()
        self.bind(selected=self._update_background)
    
    def _setup_ui(self):
        """设置UI"""
        with self.canvas.before:
            self._bg_color = Color(*self._theme.nav_background)
            self._bg_rect = RoundedRectangle(
                pos=self.pos, 
                size=self.size,
                radius=[5, 5, 5, 5]
            )
        
        self.bind(pos=self._update_rect, size=self._update_rect)
        
        # 图标标签
        self._icon_label = Label(
            text=self.icon,
            size_hint_x=None,
            width=30,
            color=self._theme.nav_text,
            font_size='18sp'
        )
        self.add_widget(self._icon_label)
        
        # 文字标签
        self._text_label = Label(
            text=self.text,
            halign='left',
            valign='middle',
            color=self._theme.nav_text,
            font_size='14sp'
        )
        self._text_label.bind(size=self._text_label.setter('text_size'))
        self.add_widget(self._text_label)
    
    def _update_rect(self, *args):
        """更新背景矩形"""
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size
    
    def _update_background(self, *args):
        """更新背景颜色"""
        if self.selected:
            self._bg_color.rgba = self._theme.nav_selected
        else:
            self._bg_color.rgba = self._theme.nav_background
    
    def on_touch_down(self, touch):
        """处理触摸事件"""
        if self.collide_point(*touch.pos):
            if self.on_select:
                self.on_select(self)
            return True
        return super().on_touch_down(touch)


class NavigationBar(BoxLayout):
    """左侧导航栏
    
    Requirements: 12.6 - 在左侧显示导航栏（全部笔记、回收站、文件夹、标签）
    """
    
    current_item = StringProperty("all_notes")
    on_item_selected = ObjectProperty(None)
    
    def __init__(self, theme: Theme = DARK_GREEN_THEME, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_x = None
        self.width = 200
        self.padding = [10, 20, 10, 20]
        self.spacing = 5
        
        self._theme = theme
        self._items: List[NavItem] = []
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        # 背景
        with self.canvas.before:
            Color(*self._theme.nav_background)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        # 应用标题
        title = Label(
            text="PDF阅读器",
            size_hint_y=None,
            height=60,
            color=self._theme.nav_text,
            font_size='20sp',
            bold=True
        )
        self.add_widget(title)
        
        # 分隔线
        self.add_widget(Widget(size_hint_y=None, height=20))
        
        # 导航项目
        nav_items = [
            ("all_notes", "📚", "全部笔记"),
            ("notes", "📝", "笔记"),
            ("pdf", "📄", "PDF"),
            ("folders", "📁", "文件夹"),
            ("tags", "🏷️", "标签"),
            ("trash", "🗑️", "回收站"),
        ]
        
        for item_id, icon, text in nav_items:
            item = NavItem(
                text=text,
                icon=icon,
                on_select=lambda x, id=item_id: self._on_item_click(id)
            )
            item.selected = (item_id == self.current_item)
            self._items.append(item)
            self.add_widget(item)
        
        # 弹性空间
        self.add_widget(Widget())
        
        # 设置按钮
        settings_item = NavItem(
            text="设置",
            icon="⚙️",
            on_select=lambda x: self._on_item_click("settings")
        )
        self._items.append(settings_item)
        self.add_widget(settings_item)
    
    def _update_bg(self, *args):
        """更新背景"""
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size
    
    def _on_item_click(self, item_id: str):
        """处理导航项点击"""
        self.current_item = item_id
        
        # 更新选中状态
        for item in self._items:
            item.selected = False
        
        # 找到对应的item并设置选中
        item_map = {
            "all_notes": 0, "notes": 1, "pdf": 2, 
            "folders": 3, "tags": 4, "trash": 5, "settings": 6
        }
        if item_id in item_map:
            idx = item_map[item_id]
            if idx < len(self._items):
                self._items[idx].selected = True
        
        if self.on_item_selected:
            self.on_item_selected(item_id)


class MainContent(ScreenManager):
    """主内容区域"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.transition = SlideTransition(duration=0.2)


class MainWindow(BoxLayout):
    """主窗口
    
    Requirements: 12.1 - 采用深绿色主题作为默认界面风格
    Requirements: 12.6 - 在左侧显示导航栏
    """
    
    theme = ObjectProperty(DARK_GREEN_THEME)
    settings = ObjectProperty(None)
    
    def __init__(self, settings: Optional[Settings] = None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        
        # 加载设置
        self.settings = settings or Settings()
        self.theme = get_theme(self.settings.theme)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        # 背景
        with self.canvas.before:
            Color(*self.theme.background)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        # 左侧导航栏
        self.nav_bar = NavigationBar(
            theme=self.theme,
            on_item_selected=self._on_nav_select
        )
        self.add_widget(self.nav_bar)
        
        # 主内容区域
        self.content = MainContent()
        self.add_widget(self.content)
        
        # 添加默认屏幕（占位）
        self._add_placeholder_screens()
    
    def _update_bg(self, *args):
        """更新背景"""
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size
    
    def _add_placeholder_screens(self):
        """添加占位屏幕"""
        screens = [
            "all_notes", "notes", "pdf", "folders", 
            "tags", "trash", "settings", "reader"
        ]
        for name in screens:
            screen = Screen(name=name)
            placeholder = Label(
                text=f"{name.replace('_', ' ').title()} View",
                color=self.theme.text_primary
            )
            screen.add_widget(placeholder)
            self.content.add_widget(screen)
    
    def _on_nav_select(self, item_id: str):
        """处理导航选择"""
        if item_id in [s.name for s in self.content.screens]:
            self.content.current = item_id
    
    def set_screen(self, screen_name: str, screen_widget: Optional[Screen] = None):
        """设置屏幕内容"""
        # 移除旧屏幕
        old_screen = self.content.get_screen(screen_name)
        if old_screen:
            self.content.remove_widget(old_screen)
        
        # 添加新屏幕
        if screen_widget:
            screen_widget.name = screen_name
            self.content.add_widget(screen_widget)
        
        self.content.current = screen_name
    
    def show_reader(self, document_path: str):
        """显示阅读器视图"""
        self.content.current = "reader"
    
    def show_file_manager(self):
        """显示文件管理器"""
        self.content.current = "all_notes"
    
    def show_settings(self):
        """显示设置"""
        self.content.current = "settings"
    
    def apply_theme(self, theme_name: str):
        """应用主题"""
        self.theme = get_theme(theme_name)
        self.settings.theme = theme_name
        # 重新绘制UI
        self._update_bg()


class PDFReaderApp(App):
    """PDF阅读器应用
    
    集成所有模块的主应用类。
    """
    
    def __init__(self, settings: Optional[Settings] = None, 
                 application: Optional['Application'] = None, **kwargs):
        super().__init__(**kwargs)
        self.settings = settings or Settings()
        self.application = application  # Application实例
        self.main_window: Optional[MainWindow] = None
        self.initial_file: Optional[Path] = None  # 启动时打开的文件
        
        # 服务引用（从Application获取）
        self._file_manager = None
        self._annotation_engine = None
        self._palm_rejection = None
        self._magnifier = None
        self._plugin_manager = None
        self._backup_service = None
    
    def build(self):
        """构建应用"""
        self.title = "华为平板PDF阅读器"
        self.main_window = MainWindow(settings=self.settings)
        
        # 初始化服务引用
        if self.application:
            self._init_services()
        
        return self.main_window
    
    def _init_services(self):
        """初始化服务引用"""
        if not self.application:
            return
        
        self._file_manager = self.application.get_file_manager()
        self._annotation_engine = self.application.get_annotation_engine()
        self._palm_rejection = self.application.get_palm_rejection()
        self._magnifier = self.application.get_magnifier()
        self._plugin_manager = self.application.get_plugin_manager()
        self._backup_service = self.application.get_backup_service()
    
    def on_start(self):
        """应用启动"""
        # 如果有初始文件，打开它
        if self.initial_file and self.initial_file.exists():
            Clock.schedule_once(lambda dt: self._open_initial_file(), 0.5)
    
    def _open_initial_file(self):
        """打开初始文件"""
        if self.initial_file and self.main_window:
            self.main_window.show_reader(str(self.initial_file))
    
    def on_stop(self):
        """应用停止"""
        # 保存设置
        if self.application:
            self.application.save_settings()
    
    # ============== 服务访问器 ==============
    
    @property
    def file_manager(self):
        """获取文件管理器"""
        return self._file_manager
    
    @property
    def annotation_engine(self):
        """获取注释引擎"""
        return self._annotation_engine
    
    @property
    def palm_rejection(self):
        """获取防误触系统"""
        return self._palm_rejection
    
    @property
    def magnifier(self):
        """获取放大镜"""
        return self._magnifier
    
    @property
    def plugin_manager(self):
        """获取插件管理器"""
        return self._plugin_manager
    
    @property
    def backup_service(self):
        """获取备份服务"""
        return self._backup_service
    
    # ============== 便捷方法 ==============
    
    def open_document(self, file_path):
        """打开文档"""
        if self.application:
            return self.application.open_document(Path(file_path))
        return None, None
    
    def translate_text(self, text: str, direction: str = "en_to_zh") -> str:
        """翻译文本"""
        if self.application:
            return self.application.translate_text(text, direction)
        return text
    
    def convert_chinese(self, text: str, direction: str = "t2s") -> str:
        """繁简转换"""
        if self.application:
            return self.application.convert_chinese(text, direction)
        return text


def run_app(settings: Optional[Settings] = None, application: Optional['Application'] = None):
    """运行应用"""
    app = PDFReaderApp(settings=settings, application=application)
    app.run()

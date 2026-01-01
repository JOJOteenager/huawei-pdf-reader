"""
华为平板PDF阅读器 - 文件管理视图

实现文档列表、缩略图、搜索框、文件夹和标签管理UI。
Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.properties import (
    ObjectProperty, StringProperty, BooleanProperty,
    ListProperty, NumericProperty
)
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from typing import Optional, Callable, List
from io import BytesIO
from datetime import datetime

from huawei_pdf_reader.ui.theme import Theme, DARK_GREEN_THEME
from huawei_pdf_reader.models import DocumentEntry, Folder, Tag


class SearchBar(BoxLayout):
    """搜索栏
    
    Requirements: 2.4 - 用户在搜索框输入关键词时搜索并显示匹配的文档
    """
    
    search_text = StringProperty("")
    on_search = ObjectProperty(None)
    
    def __init__(self, theme: Theme = DARK_GREEN_THEME, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 50
        self.padding = [10, 5, 10, 5]
        self.spacing = 10
        
        self._theme = theme
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        # 背景
        with self.canvas.before:
            Color(*self._theme.surface)
            self._bg_rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[10]
            )
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        # 搜索图标
        search_icon = Label(
            text="🔍",
            size_hint_x=None,
            width=40,
            font_size='18sp'
        )
        self.add_widget(search_icon)
        
        # 搜索输入框
        self._input = TextInput(
            hint_text="搜索文档...",
            multiline=False,
            background_color=(0, 0, 0, 0),
            foreground_color=self._theme.text_primary,
            hint_text_color=self._theme.text_hint,
            cursor_color=self._theme.accent,
            font_size='14sp'
        )
        self._input.bind(text=self._on_text_change)
        self._input.bind(on_text_validate=self._on_search_submit)
        self.add_widget(self._input)
        
        # 清除按钮
        self._clear_btn = Button(
            text="✕",
            size_hint_x=None,
            width=40,
            background_color=(0, 0, 0, 0),
            color=self._theme.text_secondary,
            opacity=0
        )
        self._clear_btn.bind(on_press=self._clear_search)
        self.add_widget(self._clear_btn)
    
    def _update_bg(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size
    
    def _on_text_change(self, instance, value):
        self.search_text = value
        self._clear_btn.opacity = 1 if value else 0
        # 延迟搜索
        Clock.unschedule(self._do_search)
        Clock.schedule_once(self._do_search, 0.3)
    
    def _do_search(self, dt):
        if self.on_search:
            self.on_search(self.search_text)
    
    def _on_search_submit(self, instance):
        if self.on_search:
            self.on_search(self.search_text)
    
    def _clear_search(self, instance):
        self._input.text = ""


class DocumentCard(BoxLayout):
    """文档卡片
    
    Requirements: 2.6 - 显示文档缩略图预览和最后修改日期
    """
    
    document = ObjectProperty(None)
    on_click = ObjectProperty(None)
    on_long_press = ObjectProperty(None)
    selected = BooleanProperty(False)
    
    def __init__(self, document: DocumentEntry, theme: Theme = DARK_GREEN_THEME, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (None, None)
        self.size = (160, 220)
        self.padding = 5
        self.spacing = 5
        
        self.document = document
        self._theme = theme
        self._touch_start_time = 0
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        # 背景
        with self.canvas.before:
            self._bg_color = Color(*self._theme.card)
            self._bg_rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[10]
            )
        self.bind(pos=self._update_bg, size=self._update_bg)
        self.bind(selected=self._update_selection)
        
        # 缩略图区域
        thumbnail_box = BoxLayout(size_hint_y=0.7)
        with thumbnail_box.canvas.before:
            Color(*self._theme.surface)
            self._thumb_bg = RoundedRectangle(
                pos=thumbnail_box.pos, 
                size=thumbnail_box.size,
                radius=[8, 8, 0, 0]
            )
        thumbnail_box.bind(
            pos=lambda i, v: setattr(self._thumb_bg, 'pos', v),
            size=lambda i, v: setattr(self._thumb_bg, 'size', v)
        )
        
        # 缩略图或占位符
        if self.document.thumbnail:
            try:
                data = BytesIO(self.document.thumbnail)
                img = CoreImage(data, ext='png')
                thumbnail = Image(texture=img.texture)
            except:
                thumbnail = Label(
                    text="📄" if self.document.file_type == 'pdf' else "📝",
                    font_size='48sp'
                )
        else:
            thumbnail = Label(
                text="📄" if self.document.file_type == 'pdf' else "📝",
                font_size='48sp'
            )
        thumbnail_box.add_widget(thumbnail)
        self.add_widget(thumbnail_box)
        
        # 文档信息
        info_box = BoxLayout(orientation='vertical', size_hint_y=0.3, padding=[5, 0])
        
        # 标题
        title = Label(
            text=self.document.title[:20] + ('...' if len(self.document.title) > 20 else ''),
            color=self._theme.text_primary,
            font_size='12sp',
            halign='left',
            valign='top',
            size_hint_y=0.6
        )
        title.bind(size=title.setter('text_size'))
        info_box.add_widget(title)
        
        # 修改日期
        date_str = self.document.modified_at.strftime("%Y-%m-%d")
        date_label = Label(
            text=date_str,
            color=self._theme.text_secondary,
            font_size='10sp',
            halign='left',
            valign='bottom',
            size_hint_y=0.4
        )
        date_label.bind(size=date_label.setter('text_size'))
        info_box.add_widget(date_label)
        
        self.add_widget(info_box)
    
    def _update_bg(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size
    
    def _update_selection(self, *args):
        if self.selected:
            self._bg_color.rgba = self._theme.accent + (0.3,)
        else:
            self._bg_color.rgba = self._theme.card
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._touch_start_time = Clock.get_time()
            Clock.schedule_once(self._check_long_press, 0.5)
            return True
        return super().on_touch_down(touch)
    
    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            Clock.unschedule(self._check_long_press)
            elapsed = Clock.get_time() - self._touch_start_time
            if elapsed < 0.5:
                if self.on_click:
                    self.on_click(self.document)
            return True
        return super().on_touch_up(touch)
    
    def _check_long_press(self, dt):
        """检查长按 - Requirements: 2.5"""
        if self.on_long_press:
            self.on_long_press(self.document)


class DocumentGrid(ScrollView):
    """文档网格视图"""
    
    documents = ListProperty([])
    on_document_click = ObjectProperty(None)
    on_document_long_press = ObjectProperty(None)
    
    def __init__(self, theme: Theme = DARK_GREEN_THEME, **kwargs):
        super().__init__(**kwargs)
        self._theme = theme
        
        self._grid = GridLayout(
            cols=4,
            spacing=15,
            padding=15,
            size_hint_y=None
        )
        self._grid.bind(minimum_height=self._grid.setter('height'))
        self.add_widget(self._grid)
        
        self.bind(documents=self._update_grid)
    
    def _update_grid(self, *args):
        """更新网格"""
        self._grid.clear_widgets()
        
        for doc in self.documents:
            card = DocumentCard(
                document=doc,
                theme=self._theme,
                on_click=self.on_document_click,
                on_long_press=self.on_document_long_press
            )
            self._grid.add_widget(card)


class FolderItem(BoxLayout):
    """文件夹项目
    
    Requirements: 2.2 - 允许创建和管理文件夹层级结构
    """
    
    folder = ObjectProperty(None)
    on_click = ObjectProperty(None)
    
    def __init__(self, folder: Folder, theme: Theme = DARK_GREEN_THEME, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 45
        self.padding = [10, 5]
        self.spacing = 10
        
        self.folder = folder
        self._theme = theme
        self._setup_ui()
    
    def _setup_ui(self):
        with self.canvas.before:
            Color(*self._theme.surface)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[5])
        self.bind(pos=lambda i, v: setattr(self._bg, 'pos', v))
        self.bind(size=lambda i, v: setattr(self._bg, 'size', v))
        
        # 图标
        icon = Label(text="📁", size_hint_x=None, width=30, font_size='18sp')
        self.add_widget(icon)
        
        # 名称
        name = Label(
            text=self.folder.name,
            color=self._theme.text_primary,
            halign='left',
            valign='middle'
        )
        name.bind(size=name.setter('text_size'))
        self.add_widget(name)
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.on_click:
                self.on_click(self.folder)
            return True
        return super().on_touch_down(touch)


class TagChip(BoxLayout):
    """标签芯片
    
    Requirements: 2.3 - 允许为文档添加和管理标签
    """
    
    tag = ObjectProperty(None)
    on_click = ObjectProperty(None)
    selected = BooleanProperty(False)
    
    def __init__(self, tag: Tag, theme: Theme = DARK_GREEN_THEME, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (100, 32)
        self.padding = [10, 5]
        
        self.tag = tag
        self._theme = theme
        self._setup_ui()
    
    def _setup_ui(self):
        # 使用标签颜色
        from huawei_pdf_reader.ui.theme import hex_to_rgba
        tag_color = hex_to_rgba(self.tag.color, 0.3)
        
        with self.canvas.before:
            self._bg_color = Color(*tag_color)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[16])
        self.bind(pos=lambda i, v: setattr(self._bg, 'pos', v))
        self.bind(size=lambda i, v: setattr(self._bg, 'size', v))
        
        label = Label(
            text=self.tag.name,
            color=self._theme.text_primary,
            font_size='12sp'
        )
        self.add_widget(label)
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.on_click:
                self.on_click(self.tag)
            return True
        return super().on_touch_down(touch)


class DocumentContextMenu(Popup):
    """文档上下文菜单
    
    Requirements: 2.5 - 长按文档项显示文档操作菜单
    """
    
    document = ObjectProperty(None)
    on_action = ObjectProperty(None)
    
    def __init__(self, document: DocumentEntry, theme: Theme = DARK_GREEN_THEME, **kwargs):
        super().__init__(**kwargs)
        self.document = document
        self._theme = theme
        
        self.title = document.title
        self.size_hint = (None, None)
        self.size = (250, 300)
        self.auto_dismiss = True
        
        self._setup_content()
    
    def _setup_content(self):
        content = BoxLayout(orientation='vertical', spacing=5, padding=10)
        
        actions = [
            ("打开", "open"),
            ("重命名", "rename"),
            ("移动到...", "move"),
            ("添加标签", "add_tag"),
            ("导出", "export"),
            ("删除", "delete"),
        ]
        
        for text, action in actions:
            btn = Button(
                text=text,
                size_hint_y=None,
                height=40,
                background_color=self._theme.surface,
                color=self._theme.text_primary if action != "delete" else self._theme.error
            )
            btn.bind(on_press=lambda x, a=action: self._on_action(a))
            content.add_widget(btn)
        
        self.content = content
    
    def _on_action(self, action: str):
        self.dismiss()
        if self.on_action:
            self.on_action(self.document, action)


class FileManagerView(Screen):
    """文件管理视图
    
    Requirements: 2.1 - 显示文档列表界面，包含全部笔记、笔记和PDF分类标签
    """
    
    documents = ListProperty([])
    folders = ListProperty([])
    tags = ListProperty([])
    current_folder = ObjectProperty(None, allownone=True)
    current_tag = ObjectProperty(None, allownone=True)
    on_document_open = ObjectProperty(None)
    
    def __init__(self, theme: Theme = DARK_GREEN_THEME, **kwargs):
        super().__init__(**kwargs)
        self._theme = theme
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 背景
        with main_layout.canvas.before:
            Color(*self._theme.background)
            self._bg = Rectangle(pos=main_layout.pos, size=main_layout.size)
        main_layout.bind(
            pos=lambda i, v: setattr(self._bg, 'pos', v),
            size=lambda i, v: setattr(self._bg, 'size', v)
        )
        
        # 顶部栏：搜索和操作按钮
        top_bar = BoxLayout(size_hint_y=None, height=60, spacing=10)
        
        # 搜索栏
        self._search_bar = SearchBar(
            theme=self._theme,
            on_search=self._on_search
        )
        top_bar.add_widget(self._search_bar)
        
        # 新建文件夹按钮
        new_folder_btn = Button(
            text="📁+",
            size_hint_x=None,
            width=50,
            background_color=self._theme.primary_color,
            font_size='18sp'
        )
        new_folder_btn.bind(on_press=self._on_new_folder)
        top_bar.add_widget(new_folder_btn)
        
        main_layout.add_widget(top_bar)
        
        # 分类标签栏
        self._category_bar = BoxLayout(size_hint_y=None, height=40, spacing=10)
        categories = [("全部", "all"), ("笔记", "notes"), ("PDF", "pdf")]
        for text, cat_id in categories:
            btn = Button(
                text=text,
                background_color=self._theme.surface,
                color=self._theme.text_primary,
                font_size='12sp'
            )
            btn.bind(on_press=lambda x, c=cat_id: self._filter_by_category(c))
            self._category_bar.add_widget(btn)
        main_layout.add_widget(self._category_bar)
        
        # 标签滚动区域
        tags_scroll = ScrollView(size_hint_y=None, height=45)
        self._tags_layout = BoxLayout(
            size_hint_x=None,
            spacing=10,
            padding=[0, 5]
        )
        self._tags_layout.bind(minimum_width=self._tags_layout.setter('width'))
        tags_scroll.add_widget(self._tags_layout)
        main_layout.add_widget(tags_scroll)
        
        # 文档网格
        self._doc_grid = DocumentGrid(
            theme=self._theme,
            on_document_click=self._on_document_click,
            on_document_long_press=self._on_document_long_press
        )
        main_layout.add_widget(self._doc_grid)
        
        self.add_widget(main_layout)
        
        # 绑定数据更新
        self.bind(documents=self._update_documents)
        self.bind(tags=self._update_tags)
    
    def _update_documents(self, *args):
        """更新文档列表"""
        self._doc_grid.documents = self.documents
    
    def _update_tags(self, *args):
        """更新标签列表"""
        self._tags_layout.clear_widgets()
        for tag in self.tags:
            chip = TagChip(
                tag=tag,
                theme=self._theme,
                on_click=self._on_tag_click
            )
            self._tags_layout.add_widget(chip)
    
    def _on_search(self, keyword: str):
        """搜索文档"""
        # 触发搜索回调
        pass
    
    def _filter_by_category(self, category: str):
        """按分类筛选"""
        pass
    
    def _on_tag_click(self, tag: Tag):
        """标签点击"""
        self.current_tag = tag
    
    def _on_document_click(self, document: DocumentEntry):
        """文档点击"""
        if self.on_document_open:
            self.on_document_open(document)
    
    def _on_document_long_press(self, document: DocumentEntry):
        """文档长按"""
        menu = DocumentContextMenu(
            document=document,
            theme=self._theme,
            on_action=self._on_document_action
        )
        menu.open()
    
    def _on_document_action(self, document: DocumentEntry, action: str):
        """处理文档操作"""
        pass
    
    def _on_new_folder(self, instance):
        """新建文件夹"""
        pass

"""
华为平板PDF阅读器 - 阅读器视图

实现文档渲染、翻页、工具栏和页码指示器。
Requirements: 12.2, 12.3, 12.4, 12.5, 12.7
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.scatter import Scatter
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line, RoundedRectangle
from kivy.graphics.texture import Texture
from kivy.properties import (
    ObjectProperty, StringProperty, BooleanProperty,
    ListProperty, NumericProperty
)
from kivy.clock import Clock
from kivy.core.window import Window
from typing import Optional, Callable, List, Tuple
from io import BytesIO
from pathlib import Path

from huawei_pdf_reader.ui.theme import Theme, DARK_GREEN_THEME
from huawei_pdf_reader.models import (
    DocumentInfo, PageInfo, PenType, Stroke, StrokePoint, Annotation
)


class ToolbarButton(Button):
    """工具栏按钮"""
    
    active = BooleanProperty(False)
    
    def __init__(self, icon: str = "", theme: Theme = DARK_GREEN_THEME, **kwargs):
        super().__init__(**kwargs)
        self.text = icon
        self.size_hint = (None, None)
        self.size = (45, 45)
        self.background_color = (0, 0, 0, 0)
        self._theme = theme
        self.bind(active=self._update_color)
        self._update_color()
    
    def _update_color(self, *args):
        if self.active:
            self.color = self._theme.toolbar_icon_active
        else:
            self.color = self._theme.toolbar_icon


class TopToolbar(BoxLayout):
    """顶部工具栏
    
    Requirements: 12.2 - 在顶部显示工具栏，包含常用注释工具
    """
    
    current_tool = StringProperty("pen")
    current_color = StringProperty("#000000")
    current_width = NumericProperty(2.0)
    on_tool_change = ObjectProperty(None)
    on_color_change = ObjectProperty(None)
    on_width_change = ObjectProperty(None)
    on_more_click = ObjectProperty(None)
    on_back_click = ObjectProperty(None)
    
    def __init__(self, theme: Theme = DARK_GREEN_THEME, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 55
        self.padding = [10, 5]
        self.spacing = 5
        
        self._theme = theme
        self._tool_buttons = {}
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        # 背景
        with self.canvas.before:
            Color(*self._theme.toolbar_background)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        # 返回按钮
        back_btn = ToolbarButton(icon="←", theme=self._theme)
        back_btn.bind(on_press=lambda x: self.on_back_click and self.on_back_click())
        self.add_widget(back_btn)
        
        # 分隔
        self.add_widget(Widget(size_hint_x=None, width=20))
        
        # 笔工具组
        pen_tools = [
            ("pen", "✒️", "钢笔"),
            ("highlighter", "🖍️", "荧光笔"),
            ("pencil", "✏️", "铅笔"),
            ("eraser", "🧹", "橡皮擦"),
        ]
        
        for tool_id, icon, tooltip in pen_tools:
            btn = ToolbarButton(icon=icon, theme=self._theme)
            btn.active = (tool_id == self.current_tool)
            btn.bind(on_press=lambda x, t=tool_id: self._select_tool(t))
            self._tool_buttons[tool_id] = btn
            self.add_widget(btn)
        
        # 分隔
        self.add_widget(Widget(size_hint_x=None, width=10))
        
        # 颜色选择
        self._color_btn = Button(
            size_hint=(None, None),
            size=(35, 35),
            background_color=(0, 0, 0, 1)
        )
        self._color_btn.bind(on_press=self._show_color_picker)
        self.add_widget(self._color_btn)
        
        # 粗细滑块
        self._width_slider = Slider(
            min=0.5,
            max=10,
            value=self.current_width,
            size_hint_x=None,
            width=100
        )
        self._width_slider.bind(value=self._on_width_change)
        self.add_widget(self._width_slider)
        
        # 弹性空间
        self.add_widget(Widget())
        
        # 更多操作按钮
        more_btn = ToolbarButton(icon="⋮", theme=self._theme)
        more_btn.bind(on_press=lambda x: self.on_more_click and self.on_more_click())
        self.add_widget(more_btn)
    
    def _update_bg(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size
    
    def _select_tool(self, tool_id: str):
        """选择工具"""
        self.current_tool = tool_id
        for tid, btn in self._tool_buttons.items():
            btn.active = (tid == tool_id)
        if self.on_tool_change:
            self.on_tool_change(tool_id)
    
    def _show_color_picker(self, instance):
        """显示颜色选择器"""
        if self.on_color_change:
            # 简单的颜色选择弹窗
            colors = [
                "#000000", "#FF0000", "#00FF00", "#0000FF",
                "#FFFF00", "#FF00FF", "#00FFFF", "#FFFFFF",
            ]
            content = BoxLayout(orientation='vertical', spacing=5, padding=10)
            color_grid = BoxLayout(spacing=5)
            for color in colors:
                from huawei_pdf_reader.ui.theme import hex_to_rgba
                btn = Button(
                    size_hint=(None, None),
                    size=(40, 40),
                    background_color=hex_to_rgba(color)
                )
                btn.bind(on_press=lambda x, c=color: self._set_color(c))
                color_grid.add_widget(btn)
            content.add_widget(color_grid)
            
            self._color_popup = Popup(
                title="选择颜色",
                content=content,
                size_hint=(None, None),
                size=(350, 150)
            )
            self._color_popup.open()
    
    def _set_color(self, color: str):
        """设置颜色"""
        self.current_color = color
        from huawei_pdf_reader.ui.theme import hex_to_rgba
        self._color_btn.background_color = hex_to_rgba(color)
        if hasattr(self, '_color_popup'):
            self._color_popup.dismiss()
        if self.on_color_change:
            self.on_color_change(color)
    
    def _on_width_change(self, instance, value):
        """粗细变化"""
        self.current_width = value
        if self.on_width_change:
            self.on_width_change(value)


class MoreActionsMenu(Popup):
    """更多操作菜单
    
    Requirements: 12.3 - 在侧边显示更多操作菜单
    Requirements: 12.4 - 点击"更多操作"显示全屏放大、页面调整、导出等选项
    """
    
    on_action = ObjectProperty(None)
    
    def __init__(self, theme: Theme = DARK_GREEN_THEME, **kwargs):
        super().__init__(**kwargs)
        self._theme = theme
        self.title = "更多操作"
        self.size_hint = (None, None)
        self.size = (280, 400)
        self.auto_dismiss = True
        
        self._setup_content()
    
    def _setup_content(self):
        content = BoxLayout(orientation='vertical', spacing=8, padding=10)
        
        actions = [
            ("全屏放大", "fullscreen", "🔍"),
            ("页面调整", "page_adjust", "📐"),
            ("旋转页面", "rotate", "🔄"),
            ("删除页面", "delete_page", "🗑️"),
            ("跳转页面", "goto_page", "📄"),
            ("添加书签", "add_bookmark", "🔖"),
            ("导出文档", "export_doc", "📤"),
            ("导出为图片", "export_image", "🖼️"),
            ("放大镜", "magnifier", "🔎"),
        ]
        
        for text, action, icon in actions:
            btn = Button(
                text=f"{icon}  {text}",
                size_hint_y=None,
                height=40,
                background_color=self._theme.surface,
                color=self._theme.text_primary,
                halign='left'
            )
            btn.bind(on_press=lambda x, a=action: self._on_action(a))
            content.add_widget(btn)
        
        self.content = content
    
    def _on_action(self, action: str):
        self.dismiss()
        if self.on_action:
            self.on_action(action)


class PageIndicator(BoxLayout):
    """页码指示器
    
    Requirements: 12.7 - 在底部显示页码指示器
    """
    
    current_page = NumericProperty(1)
    total_pages = NumericProperty(1)
    on_page_change = ObjectProperty(None)
    
    def __init__(self, theme: Theme = DARK_GREEN_THEME, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (None, None)
        self.size = (200, 40)
        self.padding = [10, 5]
        self.spacing = 10
        
        self._theme = theme
        self._setup_ui()
    
    def _setup_ui(self):
        # 背景
        with self.canvas.before:
            Color(*self._theme.surface + (0.9,))
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[20])
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        # 上一页
        prev_btn = Button(
            text="◀",
            size_hint_x=None,
            width=30,
            background_color=(0, 0, 0, 0),
            color=self._theme.text_primary
        )
        prev_btn.bind(on_press=self._prev_page)
        self.add_widget(prev_btn)
        
        # 页码显示
        self._page_label = Label(
            text=f"{self.current_page} / {self.total_pages}",
            color=self._theme.text_primary,
            font_size='14sp'
        )
        self.add_widget(self._page_label)
        
        # 下一页
        next_btn = Button(
            text="▶",
            size_hint_x=None,
            width=30,
            background_color=(0, 0, 0, 0),
            color=self._theme.text_primary
        )
        next_btn.bind(on_press=self._next_page)
        self.add_widget(next_btn)
        
        self.bind(current_page=self._update_label)
        self.bind(total_pages=self._update_label)
    
    def _update_bg(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size
    
    def _update_label(self, *args):
        self._page_label.text = f"{self.current_page} / {self.total_pages}"
    
    def _prev_page(self, instance):
        if self.current_page > 1:
            self.current_page -= 1
            if self.on_page_change:
                self.on_page_change(self.current_page)
    
    def _next_page(self, instance):
        if self.current_page < self.total_pages:
            self.current_page += 1
            if self.on_page_change:
                self.on_page_change(self.current_page)


class DocumentCanvas(RelativeLayout):
    """文档画布 - 用于渲染文档和绘制注释"""
    
    page_image = ObjectProperty(None, allownone=True)
    annotations = ListProperty([])
    current_stroke = ObjectProperty(None, allownone=True)
    drawing_enabled = BooleanProperty(True)
    
    def __init__(self, theme: Theme = DARK_GREEN_THEME, **kwargs):
        super().__init__(**kwargs)
        self._theme = theme
        self._strokes: List[Stroke] = []
        self._current_points: List[Tuple[float, float]] = []
        self._setup_ui()
    
    def _setup_ui(self):
        # 背景
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        # 页面图像
        self._page_widget = Image(
            allow_stretch=True,
            keep_ratio=True
        )
        self.add_widget(self._page_widget)
    
    def _update_bg(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size
    
    def set_page_texture(self, texture):
        """设置页面纹理"""
        self._page_widget.texture = texture
    
    def set_page_image(self, image_data: bytes):
        """设置页面图像数据"""
        from kivy.core.image import Image as CoreImage
        data = BytesIO(image_data)
        img = CoreImage(data, ext='png')
        self._page_widget.texture = img.texture
    
    def draw_stroke(self, stroke: Stroke):
        """绘制笔画"""
        if not stroke.points:
            return
        
        from huawei_pdf_reader.ui.theme import hex_to_rgba
        color = hex_to_rgba(stroke.color)
        
        points = []
        for p in stroke.points:
            points.extend([p.x, p.y])
        
        with self.canvas:
            Color(*color)
            Line(points=points, width=stroke.width)
    
    def clear_annotations(self):
        """清除所有注释"""
        self.canvas.clear()
        self._setup_ui()
    
    def redraw_annotations(self, annotations: List[Annotation]):
        """重绘所有注释"""
        self.clear_annotations()
        for annotation in annotations:
            for stroke in annotation.strokes:
                self.draw_stroke(stroke)
    
    def on_touch_down(self, touch):
        if not self.drawing_enabled:
            return super().on_touch_down(touch)
        
        if self.collide_point(*touch.pos):
            touch.grab(self)
            self._current_points = [(touch.x, touch.y)]
            return True
        return super().on_touch_down(touch)
    
    def on_touch_move(self, touch):
        if touch.grab_current is self:
            self._current_points.append((touch.x, touch.y))
            # 实时绘制
            if len(self._current_points) >= 2:
                with self.canvas:
                    Color(0, 0, 0, 1)
                    Line(
                        points=[
                            self._current_points[-2][0], self._current_points[-2][1],
                            self._current_points[-1][0], self._current_points[-1][1]
                        ],
                        width=2
                    )
            return True
        return super().on_touch_move(touch)
    
    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            # 完成笔画
            self._current_points = []
            return True
        return super().on_touch_up(touch)


class ReaderView(Screen):
    """阅读器视图
    
    Requirements: 12.2, 12.3, 12.4, 12.5, 12.7
    """
    
    document_path = StringProperty("")
    current_page = NumericProperty(1)
    total_pages = NumericProperty(1)
    zoom_level = NumericProperty(1.0)
    on_back = ObjectProperty(None)
    
    def __init__(self, theme: Theme = DARK_GREEN_THEME, **kwargs):
        super().__init__(**kwargs)
        self._theme = theme
        self._document = None
        self._renderer = None
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        main_layout = FloatLayout()
        
        # 背景
        with main_layout.canvas.before:
            Color(*self._theme.background)
            self._bg = Rectangle(pos=main_layout.pos, size=main_layout.size)
        main_layout.bind(
            pos=lambda i, v: setattr(self._bg, 'pos', v),
            size=lambda i, v: setattr(self._bg, 'size', v)
        )
        
        # 内容区域
        content_layout = BoxLayout(
            orientation='vertical',
            pos_hint={'x': 0, 'y': 0},
            size_hint=(1, 1)
        )
        
        # 顶部工具栏
        self._toolbar = TopToolbar(
            theme=self._theme,
            on_tool_change=self._on_tool_change,
            on_color_change=self._on_color_change,
            on_width_change=self._on_width_change,
            on_more_click=self._show_more_menu,
            on_back_click=self._on_back
        )
        content_layout.add_widget(self._toolbar)
        
        # 文档显示区域
        self._scroll_view = ScrollView(do_scroll_x=True, do_scroll_y=True)
        self._scatter = Scatter(
            do_rotation=False,
            do_translation=True,
            do_scale=True,
            scale_min=0.5,
            scale_max=4.0
        )
        
        self._canvas = DocumentCanvas(theme=self._theme)
        self._canvas.size_hint = (None, None)
        self._canvas.size = (800, 1200)
        
        self._scatter.add_widget(self._canvas)
        self._scroll_view.add_widget(self._scatter)
        content_layout.add_widget(self._scroll_view)
        
        main_layout.add_widget(content_layout)
        
        # 页码指示器（浮动在底部中央）
        self._page_indicator = PageIndicator(
            theme=self._theme,
            pos_hint={'center_x': 0.5, 'y': 0.02},
            on_page_change=self._goto_page
        )
        main_layout.add_widget(self._page_indicator)
        
        self.add_widget(main_layout)
        
        # 绑定属性
        self.bind(current_page=self._on_page_change)
        self.bind(total_pages=self._on_total_pages_change)
    
    def load_document(self, path: str):
        """加载文档"""
        self.document_path = path
        # 实际加载逻辑由外部处理
    
    def set_page_image(self, image_data: bytes):
        """设置当前页面图像"""
        self._canvas.set_page_image(image_data)
    
    def set_document_info(self, total_pages: int):
        """设置文档信息"""
        self.total_pages = total_pages
        self._page_indicator.total_pages = total_pages
    
    def _on_page_change(self, instance, value):
        """页码变化"""
        self._page_indicator.current_page = value
    
    def _on_total_pages_change(self, instance, value):
        """总页数变化"""
        self._page_indicator.total_pages = value
    
    def _goto_page(self, page_num: int):
        """跳转到指定页"""
        if 1 <= page_num <= self.total_pages:
            self.current_page = page_num
    
    def _on_tool_change(self, tool_id: str):
        """工具变化"""
        self._canvas.drawing_enabled = (tool_id != "eraser")
    
    def _on_color_change(self, color: str):
        """颜色变化"""
        pass
    
    def _on_width_change(self, width: float):
        """粗细变化"""
        pass
    
    def _show_more_menu(self):
        """显示更多操作菜单"""
        menu = MoreActionsMenu(
            theme=self._theme,
            on_action=self._on_more_action
        )
        menu.open()
    
    def _on_more_action(self, action: str):
        """处理更多操作"""
        if action == "goto_page":
            self._show_goto_page_dialog()
        elif action == "magnifier":
            self._activate_magnifier()
        # 其他操作...
    
    def _show_goto_page_dialog(self):
        """显示跳转页面对话框"""
        from kivy.uix.textinput import TextInput
        
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        label = Label(
            text=f"输入页码 (1-{self.total_pages}):",
            size_hint_y=None,
            height=30,
            color=self._theme.text_primary
        )
        content.add_widget(label)
        
        input_field = TextInput(
            text=str(self.current_page),
            multiline=False,
            input_filter='int',
            size_hint_y=None,
            height=40
        )
        content.add_widget(input_field)
        
        btn_layout = BoxLayout(size_hint_y=None, height=40, spacing=10)
        
        cancel_btn = Button(text="取消", background_color=self._theme.surface)
        confirm_btn = Button(text="确定", background_color=self._theme.primary_color)
        
        btn_layout.add_widget(cancel_btn)
        btn_layout.add_widget(confirm_btn)
        content.add_widget(btn_layout)
        
        popup = Popup(
            title="跳转页面",
            content=content,
            size_hint=(None, None),
            size=(300, 200)
        )
        
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        confirm_btn.bind(on_press=lambda x: self._do_goto_page(input_field.text, popup))
        
        popup.open()
    
    def _do_goto_page(self, page_str: str, popup: Popup):
        """执行跳转"""
        try:
            page = int(page_str)
            if 1 <= page <= self.total_pages:
                self.current_page = page
        except ValueError:
            pass
        popup.dismiss()
    
    def _activate_magnifier(self):
        """激活放大镜"""
        pass
    
    def _on_back(self):
        """返回"""
        if self.on_back:
            self.on_back()

"""
华为平板PDF阅读器 - 注释工具UI

实现笔工具选择器、颜色选择器、粗细调节器和橡皮擦工具。
Requirements: 3.1, 3.2, 3.3, 3.4
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle, Ellipse, Line
from kivy.properties import (
    ObjectProperty, StringProperty, BooleanProperty,
    ListProperty, NumericProperty
)
from typing import Optional, Callable, List

from huawei_pdf_reader.ui.theme import Theme, DARK_GREEN_THEME, hex_to_rgba
from huawei_pdf_reader.models import PenType


class PenButton(Button):
    """笔工具按钮
    
    Requirements: 3.1 - 使用手写笔在文档上书写时实时渲染笔迹
    Requirements: 3.2 - 选择不同的笔工具应用对应的笔触效果
    """
    
    pen_type = ObjectProperty(PenType.BALLPOINT)
    active = BooleanProperty(False)
    
    def __init__(self, pen_type: PenType, icon: str = "", 
                 theme: Theme = DARK_GREEN_THEME, **kwargs):
        super().__init__(**kwargs)
        self.pen_type = pen_type
        self.text = icon
        self.size_hint = (None, None)
        self.size = (50, 50)
        self.background_color = (0, 0, 0, 0)
        self._theme = theme
        
        self.bind(active=self._update_style)
        self._update_style()
    
    def _update_style(self, *args):
        """更新样式"""
        if self.active:
            self.color = self._theme.toolbar_icon_active
        else:
            self.color = self._theme.toolbar_icon


class PenSelector(BoxLayout):
    """笔工具选择器
    
    Requirements: 3.2 - 选择不同的笔工具（钢笔、荧光笔、铅笔等）
    """
    
    current_pen = ObjectProperty(PenType.FOUNTAIN)
    on_pen_change = ObjectProperty(None)
    
    def __init__(self, theme: Theme = DARK_GREEN_THEME, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 60
        self.spacing = 5
        self.padding = [10, 5]
        
        self._theme = theme
        self._buttons = {}
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        # 背景
        with self.canvas.before:
            Color(*self._theme.surface)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        # 笔工具列表
        pens = [
            (PenType.FOUNTAIN, "✒️", "钢笔"),
            (PenType.BALLPOINT, "🖊️", "圆珠笔"),
            (PenType.HIGHLIGHTER, "🖍️", "荧光笔"),
            (PenType.PENCIL, "✏️", "铅笔"),
            (PenType.MARKER, "🖌️", "马克笔"),
        ]
        
        for pen_type, icon, tooltip in pens:
            btn = PenButton(
                pen_type=pen_type,
                icon=icon,
                theme=self._theme
            )
            btn.active = (pen_type == self.current_pen)
            btn.bind(on_press=lambda x, p=pen_type: self._select_pen(p))
            self._buttons[pen_type] = btn
            self.add_widget(btn)
    
    def _update_bg(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size
    
    def _select_pen(self, pen_type: PenType):
        """选择笔"""
        self.current_pen = pen_type
        for pt, btn in self._buttons.items():
            btn.active = (pt == pen_type)
        if self.on_pen_change:
            self.on_pen_change(pen_type)


class ColorButton(Button):
    """颜色按钮"""
    
    color_value = StringProperty("#000000")
    selected = BooleanProperty(False)
    
    def __init__(self, color: str, theme: Theme = DARK_GREEN_THEME, **kwargs):
        super().__init__(**kwargs)
        self.color_value = color
        self.size_hint = (None, None)
        self.size = (40, 40)
        self.background_color = hex_to_rgba(color)
        self._theme = theme
        
        self.bind(selected=self._update_border)
    
    def _update_border(self, *args):
        """更新边框"""
        self.canvas.after.clear()
        if self.selected:
            with self.canvas.after:
                Color(*self._theme.accent)
                Line(
                    rectangle=(self.x, self.y, self.width, self.height),
                    width=2
                )


class ColorPicker(BoxLayout):
    """颜色选择器
    
    Requirements: 3.3 - 调整笔的颜色
    """
    
    current_color = StringProperty("#000000")
    on_color_change = ObjectProperty(None)
    
    # 预设颜色
    PRESET_COLORS = [
        "#000000", "#FFFFFF", "#FF0000", "#00FF00",
        "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF",
        "#FFA500", "#800080", "#008000", "#000080",
        "#808080", "#C0C0C0", "#800000", "#008080",
    ]
    
    def __init__(self, theme: Theme = DARK_GREEN_THEME, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (None, None)
        self.size = (200, 250)
        self.padding = 10
        self.spacing = 10
        
        self._theme = theme
        self._buttons = {}
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        # 背景
        with self.canvas.before:
            Color(*self._theme.surface)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        # 标题
        title = Label(
            text="选择颜色",
            size_hint_y=None,
            height=30,
            color=self._theme.text_primary,
            font_size='14sp'
        )
        self.add_widget(title)
        
        # 颜色网格
        grid = GridLayout(cols=4, spacing=5)
        for color in self.PRESET_COLORS:
            btn = ColorButton(color=color, theme=self._theme)
            btn.selected = (color == self.current_color)
            btn.bind(on_press=lambda x, c=color: self._select_color(c))
            self._buttons[color] = btn
            grid.add_widget(btn)
        self.add_widget(grid)
        
        # 当前颜色预览
        preview_layout = BoxLayout(size_hint_y=None, height=40, spacing=10)
        preview_label = Label(
            text="当前:",
            size_hint_x=None,
            width=50,
            color=self._theme.text_secondary
        )
        preview_layout.add_widget(preview_label)
        
        self._preview = Widget(size_hint_x=None, width=60)
        with self._preview.canvas:
            Color(*hex_to_rgba(self.current_color))
            self._preview_rect = RoundedRectangle(
                pos=self._preview.pos,
                size=self._preview.size,
                radius=[5]
            )
        self._preview.bind(
            pos=lambda i, v: setattr(self._preview_rect, 'pos', v),
            size=lambda i, v: setattr(self._preview_rect, 'size', v)
        )
        preview_layout.add_widget(self._preview)
        preview_layout.add_widget(Widget())
        
        self.add_widget(preview_layout)
    
    def _update_bg(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size
    
    def _select_color(self, color: str):
        """选择颜色"""
        self.current_color = color
        for c, btn in self._buttons.items():
            btn.selected = (c == color)
        
        # 更新预览
        self._preview.canvas.clear()
        with self._preview.canvas:
            Color(*hex_to_rgba(color))
            self._preview_rect = RoundedRectangle(
                pos=self._preview.pos,
                size=self._preview.size,
                radius=[5]
            )
        
        if self.on_color_change:
            self.on_color_change(color)


class WidthSlider(BoxLayout):
    """粗细调节器
    
    Requirements: 3.3 - 调整笔的粗细
    """
    
    current_width = NumericProperty(2.0)
    min_width = NumericProperty(0.5)
    max_width = NumericProperty(20.0)
    on_width_change = ObjectProperty(None)
    
    def __init__(self, theme: Theme = DARK_GREEN_THEME, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (None, None)
        self.size = (250, 100)
        self.padding = 10
        self.spacing = 10
        
        self._theme = theme
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        # 背景
        with self.canvas.before:
            Color(*self._theme.surface)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        # 标题和数值
        header = BoxLayout(size_hint_y=None, height=25)
        title = Label(
            text="笔迹粗细",
            color=self._theme.text_primary,
            font_size='14sp',
            halign='left'
        )
        title.bind(size=title.setter('text_size'))
        header.add_widget(title)
        
        self._value_label = Label(
            text=f"{self.current_width:.1f}",
            color=self._theme.text_secondary,
            font_size='12sp',
            size_hint_x=None,
            width=50
        )
        header.add_widget(self._value_label)
        self.add_widget(header)
        
        # 滑块
        self._slider = Slider(
            min=self.min_width,
            max=self.max_width,
            value=self.current_width,
            size_hint_y=None,
            height=30
        )
        self._slider.bind(value=self._on_slider_change)
        self.add_widget(self._slider)
        
        # 预览线条
        self._preview = Widget(size_hint_y=None, height=30)
        self._draw_preview()
        self.add_widget(self._preview)
    
    def _update_bg(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size
    
    def _on_slider_change(self, instance, value):
        """滑块值变化"""
        self.current_width = value
        self._value_label.text = f"{value:.1f}"
        self._draw_preview()
        if self.on_width_change:
            self.on_width_change(value)
    
    def _draw_preview(self):
        """绘制预览线条"""
        self._preview.canvas.clear()
        with self._preview.canvas:
            Color(*self._theme.text_primary)
            Line(
                points=[
                    self._preview.x + 20, self._preview.center_y,
                    self._preview.right - 20, self._preview.center_y
                ],
                width=self.current_width
            )


class EraserTool(BoxLayout):
    """橡皮擦工具
    
    Requirements: 3.4 - 使用橡皮擦工具擦除选中区域的注释
    """
    
    eraser_size = NumericProperty(20.0)
    active = BooleanProperty(False)
    on_size_change = ObjectProperty(None)
    on_activate = ObjectProperty(None)
    
    def __init__(self, theme: Theme = DARK_GREEN_THEME, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (None, None)
        self.size = (200, 150)
        self.padding = 10
        self.spacing = 10
        
        self._theme = theme
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        # 背景
        with self.canvas.before:
            Color(*self._theme.surface)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        # 标题
        title = Label(
            text="橡皮擦",
            size_hint_y=None,
            height=25,
            color=self._theme.text_primary,
            font_size='14sp'
        )
        self.add_widget(title)
        
        # 激活按钮
        self._activate_btn = Button(
            text="🧹 启用橡皮擦",
            size_hint_y=None,
            height=40,
            background_color=self._theme.primary_color if not self.active else self._theme.accent
        )
        self._activate_btn.bind(on_press=self._toggle_active)
        self.add_widget(self._activate_btn)
        
        # 大小调节
        size_layout = BoxLayout(size_hint_y=None, height=30, spacing=10)
        size_label = Label(
            text="大小:",
            size_hint_x=None,
            width=50,
            color=self._theme.text_secondary
        )
        size_layout.add_widget(size_label)
        
        self._size_slider = Slider(
            min=5,
            max=50,
            value=self.eraser_size
        )
        self._size_slider.bind(value=self._on_size_change)
        size_layout.add_widget(self._size_slider)
        
        self._size_value = Label(
            text=f"{int(self.eraser_size)}",
            size_hint_x=None,
            width=30,
            color=self._theme.text_secondary
        )
        size_layout.add_widget(self._size_value)
        
        self.add_widget(size_layout)
        
        # 预览
        self._preview = Widget(size_hint_y=None, height=40)
        self._draw_preview()
        self.add_widget(self._preview)
    
    def _update_bg(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size
    
    def _toggle_active(self, instance):
        """切换激活状态"""
        self.active = not self.active
        if self.active:
            self._activate_btn.text = "🧹 橡皮擦已启用"
            self._activate_btn.background_color = self._theme.accent
        else:
            self._activate_btn.text = "🧹 启用橡皮擦"
            self._activate_btn.background_color = self._theme.primary_color
        
        if self.on_activate:
            self.on_activate(self.active)
    
    def _on_size_change(self, instance, value):
        """大小变化"""
        self.eraser_size = value
        self._size_value.text = f"{int(value)}"
        self._draw_preview()
        if self.on_size_change:
            self.on_size_change(value)
    
    def _draw_preview(self):
        """绘制预览"""
        self._preview.canvas.clear()
        with self._preview.canvas:
            Color(*self._theme.text_secondary + (0.5,))
            Ellipse(
                pos=(
                    self._preview.center_x - self.eraser_size / 2,
                    self._preview.center_y - self.eraser_size / 2
                ),
                size=(self.eraser_size, self.eraser_size)
            )


class AnnotationToolbar(BoxLayout):
    """注释工具栏 - 整合所有注释工具
    
    Requirements: 3.1, 3.2, 3.3, 3.4
    """
    
    current_pen = ObjectProperty(PenType.FOUNTAIN)
    current_color = StringProperty("#000000")
    current_width = NumericProperty(2.0)
    eraser_active = BooleanProperty(False)
    
    on_pen_change = ObjectProperty(None)
    on_color_change = ObjectProperty(None)
    on_width_change = ObjectProperty(None)
    on_eraser_toggle = ObjectProperty(None)
    
    def __init__(self, theme: Theme = DARK_GREEN_THEME, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 60
        self.padding = [10, 5]
        self.spacing = 10
        
        self._theme = theme
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        # 背景
        with self.canvas.before:
            Color(*self._theme.toolbar_background)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        # 笔选择器
        self._pen_selector = PenSelector(
            theme=self._theme,
            on_pen_change=self._on_pen_select
        )
        self.add_widget(self._pen_selector)
        
        # 分隔
        self.add_widget(Widget(size_hint_x=None, width=10))
        
        # 颜色按钮
        self._color_btn = Button(
            size_hint=(None, None),
            size=(40, 40),
            background_color=hex_to_rgba(self.current_color)
        )
        self._color_btn.bind(on_press=self._show_color_picker)
        self.add_widget(self._color_btn)
        
        # 粗细按钮
        self._width_btn = Button(
            text="━",
            size_hint=(None, None),
            size=(40, 40),
            background_color=(0, 0, 0, 0),
            color=self._theme.toolbar_icon
        )
        self._width_btn.bind(on_press=self._show_width_slider)
        self.add_widget(self._width_btn)
        
        # 橡皮擦按钮
        self._eraser_btn = Button(
            text="🧹",
            size_hint=(None, None),
            size=(40, 40),
            background_color=(0, 0, 0, 0),
            color=self._theme.toolbar_icon
        )
        self._eraser_btn.bind(on_press=self._toggle_eraser)
        self.add_widget(self._eraser_btn)
        
        # 弹性空间
        self.add_widget(Widget())
    
    def _update_bg(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size
    
    def _on_pen_select(self, pen_type: PenType):
        """笔选择"""
        self.current_pen = pen_type
        self.eraser_active = False
        self._eraser_btn.color = self._theme.toolbar_icon
        if self.on_pen_change:
            self.on_pen_change(pen_type)
    
    def _show_color_picker(self, instance):
        """显示颜色选择器"""
        picker = ColorPicker(
            theme=self._theme,
            on_color_change=self._on_color_select
        )
        picker.current_color = self.current_color
        
        self._color_popup = Popup(
            title="",
            content=picker,
            size_hint=(None, None),
            size=(220, 280),
            separator_height=0
        )
        self._color_popup.open()
    
    def _on_color_select(self, color: str):
        """颜色选择"""
        self.current_color = color
        self._color_btn.background_color = hex_to_rgba(color)
        if hasattr(self, '_color_popup'):
            self._color_popup.dismiss()
        if self.on_color_change:
            self.on_color_change(color)
    
    def _show_width_slider(self, instance):
        """显示粗细调节器"""
        slider = WidthSlider(
            theme=self._theme,
            on_width_change=self._on_width_select
        )
        slider.current_width = self.current_width
        
        self._width_popup = Popup(
            title="",
            content=slider,
            size_hint=(None, None),
            size=(270, 130),
            separator_height=0
        )
        self._width_popup.open()
    
    def _on_width_select(self, width: float):
        """粗细选择"""
        self.current_width = width
        if self.on_width_change:
            self.on_width_change(width)
    
    def _toggle_eraser(self, instance):
        """切换橡皮擦"""
        self.eraser_active = not self.eraser_active
        if self.eraser_active:
            self._eraser_btn.color = self._theme.toolbar_icon_active
        else:
            self._eraser_btn.color = self._theme.toolbar_icon
        
        if self.on_eraser_toggle:
            self.on_eraser_toggle(self.eraser_active)

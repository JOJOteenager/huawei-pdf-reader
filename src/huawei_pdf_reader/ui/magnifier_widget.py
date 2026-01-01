"""
华为平板PDF阅读器 - 放大镜UI组件

实现可拖动的放大镜组件、区域选择UI、翻译/转换操作按钮和结果弹窗。
Requirements: 5.1, 5.2, 5.3, 5.6, 5.7, 6.3
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.scatter import Scatter
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.graphics import (
    Color, Rectangle, RoundedRectangle, Ellipse, 
    Line, StencilPush, StencilUse, StencilUnUse, StencilPop
)
from kivy.graphics.texture import Texture
from kivy.properties import (
    ObjectProperty, StringProperty, BooleanProperty,
    ListProperty, NumericProperty
)
from kivy.clock import Clock
from typing import Optional, Callable, Tuple

from huawei_pdf_reader.ui.theme import Theme, DARK_GREEN_THEME, hex_to_rgba
from huawei_pdf_reader.models import MagnifierAction, MagnifierConfig, MagnifierResult


class MagnifierLens(Widget):
    """放大镜镜头
    
    Requirements: 5.1 - 激活放大镜工具时显示一个可拖动的放大区域
    Requirements: 5.2 - 拖动放大镜时实时显示放大后的文档内容
    """
    
    zoom_level = NumericProperty(2.0)
    source_texture = ObjectProperty(None, allownone=True)
    lens_size = NumericProperty(150)
    shape = StringProperty("circle")  # circle or rectangle
    
    def __init__(self, theme: Theme = DARK_GREEN_THEME, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (self.lens_size, self.lens_size)
        
        self._theme = theme
        self._setup_graphics()
        
        self.bind(pos=self._update_graphics)
        self.bind(size=self._update_graphics)
        self.bind(lens_size=self._on_size_change)
    
    def _setup_graphics(self):
        """设置图形"""
        self.canvas.clear()
        
        with self.canvas:
            # 边框
            Color(*self._theme.accent)
            if self.shape == "circle":
                self._border = Line(
                    circle=(self.center_x, self.center_y, self.lens_size / 2),
                    width=2
                )
            else:
                self._border = Line(
                    rectangle=(self.x, self.y, self.width, self.height),
                    width=2
                )
            
            # 内部背景
            Color(1, 1, 1, 0.95)
            if self.shape == "circle":
                self._bg = Ellipse(pos=self.pos, size=self.size)
            else:
                self._bg = Rectangle(pos=self.pos, size=self.size)
    
    def _update_graphics(self, *args):
        """更新图形"""
        if self.shape == "circle":
            self._border.circle = (self.center_x, self.center_y, self.lens_size / 2)
            self._bg.pos = self.pos
            self._bg.size = self.size
        else:
            self._border.rectangle = (self.x, self.y, self.width, self.height)
            self._bg.pos = self.pos
            self._bg.size = self.size
    
    def _on_size_change(self, instance, value):
        """大小变化"""
        self.size = (value, value)
        self._setup_graphics()
    
    def set_magnified_content(self, texture):
        """设置放大内容"""
        self.source_texture = texture
        # 在实际实现中，这里会渲染放大的内容


class RegionSelector(Widget):
    """区域选择器
    
    Requirements: 5.3 - 在放大镜中选择文本区域时识别并提取该区域的文字
    """
    
    selection_rect = ListProperty([0, 0, 0, 0])  # x, y, width, height
    on_selection_complete = ObjectProperty(None)
    active = BooleanProperty(False)
    
    def __init__(self, theme: Theme = DARK_GREEN_THEME, **kwargs):
        super().__init__(**kwargs)
        self._theme = theme
        self._start_pos = None
        self._setup_graphics()
    
    def _setup_graphics(self):
        """设置图形"""
        with self.canvas:
            Color(*self._theme.accent + (0.3,))
            self._selection_rect = Rectangle(pos=(0, 0), size=(0, 0))
            Color(*self._theme.accent)
            self._selection_border = Line(rectangle=(0, 0, 0, 0), width=2)
    
    def _update_selection(self):
        """更新选择区域显示"""
        x, y, w, h = self.selection_rect
        self._selection_rect.pos = (x, y)
        self._selection_rect.size = (w, h)
        self._selection_border.rectangle = (x, y, w, h)
    
    def on_touch_down(self, touch):
        if not self.active:
            return super().on_touch_down(touch)
        
        if self.collide_point(*touch.pos):
            touch.grab(self)
            self._start_pos = touch.pos
            self.selection_rect = [touch.x, touch.y, 0, 0]
            return True
        return super().on_touch_down(touch)
    
    def on_touch_move(self, touch):
        if touch.grab_current is self and self._start_pos:
            x = min(self._start_pos[0], touch.x)
            y = min(self._start_pos[1], touch.y)
            w = abs(touch.x - self._start_pos[0])
            h = abs(touch.y - self._start_pos[1])
            self.selection_rect = [x, y, w, h]
            self._update_selection()
            return True
        return super().on_touch_move(touch)
    
    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            if self.on_selection_complete and self.selection_rect[2] > 10 and self.selection_rect[3] > 10:
                self.on_selection_complete(tuple(self.selection_rect))
            self._start_pos = None
            return True
        return super().on_touch_up(touch)
    
    def clear_selection(self):
        """清除选择"""
        self.selection_rect = [0, 0, 0, 0]
        self._update_selection()


class ActionButton(Button):
    """操作按钮"""
    
    action = ObjectProperty(MagnifierAction.MAGNIFY)
    
    def __init__(self, action: MagnifierAction, icon: str, text: str,
                 theme: Theme = DARK_GREEN_THEME, **kwargs):
        super().__init__(**kwargs)
        self.action = action
        self.text = f"{icon}\n{text}"
        self.size_hint = (None, None)
        self.size = (70, 60)
        self.background_color = theme.surface
        self.color = theme.text_primary
        self.font_size = '11sp'
        self.halign = 'center'


class ActionBar(BoxLayout):
    """操作按钮栏
    
    Requirements: 5.6 - 翻译完成时在弹出窗口中显示翻译结果
    Requirements: 6.3 - 转换完成时显示转换后的文本供用户查看
    """
    
    on_action = ObjectProperty(None)
    
    def __init__(self, theme: Theme = DARK_GREEN_THEME, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 70
        self.spacing = 5
        self.padding = [10, 5]
        
        self._theme = theme
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        # 背景
        with self.canvas.before:
            Color(*self._theme.surface)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        # 操作按钮
        actions = [
            (MagnifierAction.TRANSLATE_EN_ZH, "🔤", "英译汉"),
            (MagnifierAction.TRANSLATE_ZH_EN, "🔠", "汉译英"),
            (MagnifierAction.CONVERT_T2S, "繁", "繁转简"),
            (MagnifierAction.CONVERT_S2T, "简", "简转繁"),
        ]
        
        for action, icon, text in actions:
            btn = ActionButton(
                action=action,
                icon=icon,
                text=text,
                theme=self._theme
            )
            btn.bind(on_press=lambda x, a=action: self._on_action(a))
            self.add_widget(btn)
    
    def _update_bg(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size
    
    def _on_action(self, action: MagnifierAction):
        """处理操作"""
        if self.on_action:
            self.on_action(action)


class ResultPopup(Popup):
    """结果弹窗
    
    Requirements: 5.6 - 翻译完成时在弹出窗口中显示翻译结果
    Requirements: 5.7 - 文字识别失败时显示"无法识别文字"的提示
    Requirements: 6.3 - 转换完成时显示转换后的文本供用户查看
    """
    
    result = ObjectProperty(None)
    on_copy = ObjectProperty(None)
    
    def __init__(self, result: MagnifierResult, theme: Theme = DARK_GREEN_THEME, **kwargs):
        super().__init__(**kwargs)
        self.result = result
        self._theme = theme
        
        # 设置标题
        action_titles = {
            MagnifierAction.TRANSLATE_EN_ZH: "英译汉结果",
            MagnifierAction.TRANSLATE_ZH_EN: "汉译英结果",
            MagnifierAction.CONVERT_T2S: "繁转简结果",
            MagnifierAction.CONVERT_S2T: "简转繁结果",
            MagnifierAction.MAGNIFY: "识别结果",
        }
        self.title = action_titles.get(result.action, "结果")
        
        self.size_hint = (None, None)
        self.size = (350, 300)
        self.auto_dismiss = True
        
        self._setup_content()
    
    def _setup_content(self):
        """设置内容"""
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        if not self.result.success:
            # 错误信息
            error_label = Label(
                text=self.result.error_message or "无法识别文字",
                color=self._theme.error,
                font_size='14sp'
            )
            content.add_widget(error_label)
        else:
            # 原文
            if self.result.original_text:
                original_box = BoxLayout(orientation='vertical', size_hint_y=0.4)
                original_title = Label(
                    text="原文:",
                    size_hint_y=None,
                    height=25,
                    color=self._theme.text_secondary,
                    font_size='12sp',
                    halign='left'
                )
                original_title.bind(size=original_title.setter('text_size'))
                original_box.add_widget(original_title)
                
                original_text = Label(
                    text=self.result.original_text[:200] + ('...' if len(self.result.original_text) > 200 else ''),
                    color=self._theme.text_primary,
                    font_size='13sp',
                    halign='left',
                    valign='top'
                )
                original_text.bind(size=original_text.setter('text_size'))
                original_box.add_widget(original_text)
                content.add_widget(original_box)
            
            # 分隔线
            content.add_widget(Widget(size_hint_y=None, height=1))
            
            # 结果
            result_box = BoxLayout(orientation='vertical', size_hint_y=0.4)
            result_title = Label(
                text="结果:",
                size_hint_y=None,
                height=25,
                color=self._theme.text_secondary,
                font_size='12sp',
                halign='left'
            )
            result_title.bind(size=result_title.setter('text_size'))
            result_box.add_widget(result_title)
            
            result_text = Label(
                text=self.result.result_text[:200] + ('...' if len(self.result.result_text) > 200 else ''),
                color=self._theme.accent,
                font_size='14sp',
                halign='left',
                valign='top',
                bold=True
            )
            result_text.bind(size=result_text.setter('text_size'))
            result_box.add_widget(result_text)
            content.add_widget(result_box)
        
        # 按钮栏
        btn_layout = BoxLayout(size_hint_y=None, height=45, spacing=10)
        
        if self.result.success:
            copy_btn = Button(
                text="复制结果",
                background_color=self._theme.primary_color,
                color=self._theme.text_primary
            )
            copy_btn.bind(on_press=self._copy_result)
            btn_layout.add_widget(copy_btn)
        
        close_btn = Button(
            text="关闭",
            background_color=self._theme.surface,
            color=self._theme.text_primary
        )
        close_btn.bind(on_press=lambda x: self.dismiss())
        btn_layout.add_widget(close_btn)
        
        content.add_widget(btn_layout)
        self.content = content
    
    def _copy_result(self, instance):
        """复制结果"""
        if self.on_copy:
            self.on_copy(self.result.result_text)
        # 尝试复制到剪贴板
        try:
            from kivy.core.clipboard import Clipboard
            Clipboard.copy(self.result.result_text)
        except:
            pass


class MagnifierWidget(FloatLayout):
    """放大镜组件
    
    整合放大镜镜头、区域选择和操作按钮。
    Requirements: 5.1, 5.2, 5.3, 5.6, 5.7, 6.3
    """
    
    active = BooleanProperty(False)
    zoom_level = NumericProperty(2.0)
    lens_size = NumericProperty(150)
    shape = StringProperty("circle")
    
    on_region_selected = ObjectProperty(None)
    on_action_requested = ObjectProperty(None)
    
    def __init__(self, theme: Theme = DARK_GREEN_THEME, **kwargs):
        super().__init__(**kwargs)
        self._theme = theme
        self._selected_region: Optional[Tuple[float, float, float, float]] = None
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        # 放大镜镜头（可拖动）
        self._lens = MagnifierLens(
            theme=self._theme,
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self._lens.zoom_level = self.zoom_level
        self._lens.lens_size = self.lens_size
        self._lens.shape = self.shape
        
        # 使用Scatter使其可拖动
        self._scatter = Scatter(
            do_rotation=False,
            do_scale=False,
            size_hint=(None, None),
            size=(self.lens_size, self.lens_size),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self._scatter.add_widget(self._lens)
        self.add_widget(self._scatter)
        
        # 区域选择器
        self._region_selector = RegionSelector(
            theme=self._theme,
            on_selection_complete=self._on_region_selected
        )
        self.add_widget(self._region_selector)
        
        # 操作按钮栏（底部）
        self._action_bar = ActionBar(
            theme=self._theme,
            pos_hint={'center_x': 0.5, 'y': 0.02},
            on_action=self._on_action
        )
        self.add_widget(self._action_bar)
        
        # 关闭按钮
        self._close_btn = Button(
            text="✕",
            size_hint=(None, None),
            size=(40, 40),
            pos_hint={'right': 0.98, 'top': 0.98},
            background_color=self._theme.error,
            color=(1, 1, 1, 1)
        )
        self._close_btn.bind(on_press=lambda x: self.deactivate())
        self.add_widget(self._close_btn)
        
        # 初始隐藏
        self.opacity = 0
        self.disabled = True
        
        self.bind(active=self._on_active_change)
    
    def _on_active_change(self, instance, value):
        """激活状态变化"""
        if value:
            self.opacity = 1
            self.disabled = False
            self._region_selector.active = True
        else:
            self.opacity = 0
            self.disabled = True
            self._region_selector.active = False
            self._region_selector.clear_selection()
    
    def activate(self, config: Optional[MagnifierConfig] = None):
        """激活放大镜
        
        Requirements: 5.1 - 激活放大镜工具时显示一个可拖动的放大区域
        """
        if config:
            self.zoom_level = config.zoom_level
            self.lens_size = config.size[0]
            self.shape = config.shape
            self._lens.zoom_level = config.zoom_level
            self._lens.lens_size = config.size[0]
            self._lens.shape = config.shape
        
        self.active = True
    
    def deactivate(self):
        """关闭放大镜"""
        self.active = False
        self._selected_region = None
    
    def _on_region_selected(self, region: Tuple[float, float, float, float]):
        """区域选择完成
        
        Requirements: 5.3 - 在放大镜中选择文本区域时识别并提取该区域的文字
        """
        self._selected_region = region
        if self.on_region_selected:
            self.on_region_selected(region)
    
    def _on_action(self, action: MagnifierAction):
        """处理操作请求"""
        if self._selected_region and self.on_action_requested:
            self.on_action_requested(action, self._selected_region)
    
    def show_result(self, result: MagnifierResult):
        """显示结果
        
        Requirements: 5.6 - 翻译完成时在弹出窗口中显示翻译结果
        Requirements: 5.7 - 文字识别失败时显示"无法识别文字"的提示
        Requirements: 6.3 - 转换完成时显示转换后的文本供用户查看
        """
        popup = ResultPopup(result=result, theme=self._theme)
        popup.open()
    
    def set_magnified_texture(self, texture):
        """设置放大内容纹理
        
        Requirements: 5.2 - 拖动放大镜时实时显示放大后的文档内容
        """
        self._lens.set_magnified_content(texture)

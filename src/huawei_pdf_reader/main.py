"""
PDF阅读器 - 主入口
支持PDF/Word文档阅读、手写笔注释、翻译和繁简转换
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.utils import get_color_from_hex


class PDFReaderApp(App):
    """PDF阅读器应用"""
    
    title = 'PDF阅读器'
    
    def build(self):
        # 深绿色主题
        Window.clearcolor = get_color_from_hex('#1B5E20')
        
        # 主布局
        root = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # 标题区域
        header = BoxLayout(size_hint_y=0.15)
        title_label = Label(
            text='PDF阅读器',
            font_size='28sp',
            bold=True,
            color=get_color_from_hex('#FFFFFF')
        )
        header.add_widget(title_label)
        root.add_widget(header)
        
        # 版本信息
        version_box = BoxLayout(size_hint_y=0.08)
        version_label = Label(
            text='版本 0.1.0',
            font_size='14sp',
            color=get_color_from_hex('#A5D6A7')
        )
        version_box.add_widget(version_label)
        root.add_widget(version_box)
        
        # 功能列表
        features_box = BoxLayout(orientation='vertical', size_hint_y=0.45, spacing=8)
        
        features = [
            '📄 支持PDF和Word文档阅读',
            '✏️ 华为手写笔注释功能',
            '🖐️ 智能防误触系统',
            '🔍 放大镜辅助查阅',
            '🌐 英汉互译功能',
            '📝 繁简中文转换',
            '📁 文档管理和标签',
            '☁️ 云端备份支持'
        ]
        
        for feature in features:
            feat_label = Label(
                text=feature,
                font_size='16sp',
                color=get_color_from_hex('#E8F5E9'),
                halign='left',
                valign='middle'
            )
            feat_label.bind(size=feat_label.setter('text_size'))
            features_box.add_widget(feat_label)
        
        root.add_widget(features_box)
        
        # 状态标签
        self.status_label = Label(
            text='应用已就绪',
            font_size='14sp',
            color=get_color_from_hex('#81C784'),
            size_hint_y=0.1
        )
        root.add_widget(self.status_label)
        
        # 按钮区域
        btn_box = BoxLayout(size_hint_y=0.15, spacing=10)
        
        # 开始按钮
        start_btn = Button(
            text='开始使用',
            font_size='18sp',
            background_color=get_color_from_hex('#4CAF50'),
            background_normal=''
        )
        start_btn.bind(on_press=self.on_start)
        btn_box.add_widget(start_btn)
        
        root.add_widget(btn_box)
        
        return root
    
    def on_start(self, instance):
        """开始按钮点击"""
        self.status_label.text = '功能开发中，敬请期待...'
        self.status_label.color = get_color_from_hex('#FFEB3B')


def main():
    """主入口函数"""
    PDFReaderApp().run()


if __name__ == '__main__':
    main()
